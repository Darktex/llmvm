#!/usr/bin/env python3
"""Analyze LLMVM and HomeAssistant metrics from logs."""

import re
import sys
import argparse
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any


def parse_ha_metrics(log_file: str) -> List[Dict[str, Any]]:
    """Parse HomeAssistant LLMVM_METRICS logs."""
    pattern = r'LLMVM_METRICS:.*?agent_overhead_ms=([\d.]+).*?llmvm_latency_ms=([\d.]+).*?response_overhead_ms=([\d.]+).*?total_ms=([\d.]+)'

    metrics = []
    with open(log_file, 'r', errors='ignore') as f:
        for line in f:
            if 'LLMVM_METRICS:' in line:
                match = re.search(pattern, line)
                if match:
                    metrics.append({
                        'agent_overhead': float(match.group(1)),
                        'llmvm_latency': float(match.group(2)),
                        'response_overhead': float(match.group(3)),
                        'total': float(match.group(4))
                    })
    return metrics


def parse_llmvm_metrics(log_file: str) -> List[Dict[str, Any]]:
    """Parse LLMVM server metrics."""
    # Try to match various patterns
    patterns = [
        r'LLMVM_SERVER_METRICS:.*?llm_agent_total=([\d.]+)ms.*?total=([\d.]+)ms',
        r'LLMVM_SERVER_METRICS:.*?llm_direct=([\d.]+)ms.*?total=([\d.]+)ms',
    ]

    metrics = []
    with open(log_file, 'r', errors='ignore') as f:
        for line in f:
            if 'LLMVM_SERVER_METRICS:' in line:
                for pattern in patterns:
                    match = re.search(pattern, line)
                    if match:
                        metrics.append({
                            'llm_processing': float(match.group(1)),
                            'total': float(match.group(2))
                        })
                        break
    return metrics


def calculate_stats(values: List[float]) -> Dict[str, float]:
    """Calculate statistical measures."""
    if not values:
        return {}

    sorted_vals = sorted(values)
    n = len(sorted_vals)

    return {
        'avg': sum(sorted_vals) / n,
        'min': sorted_vals[0],
        'max': sorted_vals[-1],
        'p50': sorted_vals[n // 2],
        'p95': sorted_vals[int(n * 0.95)] if n > 20 else sorted_vals[-1],
        'p99': sorted_vals[int(n * 0.99)] if n > 100 else sorted_vals[-1],
    }


def analyze(metrics: List[Dict[str, Any]], label: str):
    """Print statistics."""
    if not metrics:
        print(f"\n⚠️  No {label} metrics found")
        return

    print(f"\n{label} Statistics ({len(metrics)} requests):")
    print("=" * 80)

    # Calculate stats for each metric
    all_keys = set()
    for m in metrics:
        all_keys.update(m.keys())

    for key in sorted(all_keys):
        values = [m[key] for m in metrics if key in m]
        if not values:
            continue

        stats = calculate_stats(values)

        print(f"{key:25s}: avg={stats['avg']:8.1f}ms  "
              f"p50={stats['p50']:8.1f}ms  "
              f"p95={stats['p95']:8.1f}ms  "
              f"min={stats['min']:8.1f}ms  "
              f"max={stats['max']:8.1f}ms")


def main():
    parser = argparse.ArgumentParser(description='Analyze LLMVM and HomeAssistant metrics')
    parser.add_argument('--ha-log', default='/config/home-assistant.log',
                        help='Path to HomeAssistant log file')
    parser.add_argument('--llmvm-log', default=str(Path.home() / '.local/share/llmvm/logs/server.log'),
                        help='Path to LLMVM server log file')
    parser.add_argument('--tail', type=int, default=0,
                        help='Only analyze last N lines of each log')

    args = parser.parse_args()

    print("📊 LLMVM Phase 1 Metrics Analysis")
    print("=" * 80)
    print(f"Analyzing logs:")
    print(f"  HomeAssistant: {args.ha_log}")
    print(f"  LLMVM Server:  {args.llmvm_log}")

    # Parse metrics
    ha_metrics = parse_ha_metrics(args.ha_log)
    llmvm_metrics = parse_llmvm_metrics(args.llmvm_log)

    if args.tail > 0:
        ha_metrics = ha_metrics[-args.tail:]
        llmvm_metrics = llmvm_metrics[-args.tail:]

    # Analyze
    analyze(ha_metrics, "HomeAssistant Conversation Agent")
    analyze(llmvm_metrics, "LLMVM Server")

    # Combined analysis
    if ha_metrics:
        print(f"\n🎯 Bottleneck Analysis:")
        print("=" * 80)

        avg_agent = sum(m['agent_overhead'] for m in ha_metrics) / len(ha_metrics)
        avg_llmvm = sum(m['llmvm_latency'] for m in ha_metrics) / len(ha_metrics)
        avg_response = sum(m['response_overhead'] for m in ha_metrics) / len(ha_metrics)
        avg_total = sum(m['total'] for m in ha_metrics) / len(ha_metrics)

        components = [
            ("Agent Overhead", avg_agent),
            ("LLMVM Processing", avg_llmvm),
            ("Response Overhead", avg_response),
        ]

        for name, latency in components:
            pct = (latency / avg_total * 100) if avg_total > 0 else 0
            print(f"{name:25s}: {latency:8.1f}ms  ({pct:5.1f}% of total)")

        print(f"\n{'Total Latency':25s}: {avg_total:8.1f}ms")

        # Recommendations
        print(f"\n💡 Phase 2 Optimization Recommendations:")
        print("=" * 80)

        if avg_llmvm > 1000:
            print(f"✅ LLM Inference is the primary bottleneck ({avg_llmvm:.0f}ms)")
            print(f"   → Switch to TensorRT-LLM + NVFP4 (3-4x speedup expected)")
            print(f"   → Disable thinking mode (system prompts)")
            print(f"   → Use faster model (Qwen2.5-72B vs GPT-OSS-120B)")

        if avg_agent > 10:
            print(f"⚠️  Agent overhead is high ({avg_agent:.1f}ms)")
            print(f"   → Optimize tool discovery")
            print(f"   → Reduce number of tools in prompt")

        if avg_response > 10:
            print(f"⚠️  Response overhead is high ({avg_response:.1f}ms)")
            print(f"   → Review message parsing logic")

        # Expected improvements
        print(f"\n🎯 Expected Phase 2 Improvements:")
        print("=" * 80)
        current_total = avg_total
        target_llm = avg_llmvm / 3.5  # NVFP4 speedup
        target_total = avg_agent + target_llm + avg_response

        print(f"Current Total:  {current_total:8.1f}ms")
        print(f"Target Total:   {target_total:8.1f}ms  ({target_total/current_total*100:.0f}% of current)")
        print(f"Improvement:    {current_total - target_total:8.1f}ms  ({(1 - target_total/current_total)*100:.0f}% reduction)")

    else:
        print(f"\n⚠️  No metrics found. Have you:")
        print(f"  1. Added timing instrumentation to conversation.py?")
        print(f"  2. Enabled debug logging in HomeAssistant?")
        print(f"  3. Run any test queries?")


if __name__ == "__main__":
    main()
