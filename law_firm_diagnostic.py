#!/usr/bin/env python3
"""
Gabe Gross Consulting - Law Firm Profitability Diagnostic Tool

A command-line tool for analyzing mid-sized law firm profitability
and identifying opportunities for improvement.
"""

import sys
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Tuple
import re


# ============================================================================
# CONFIGURATION & BENCHMARKS
# ============================================================================

@dataclass
class Benchmarks:
    """Industry benchmarks for mid-sized law firms (20-150 attorneys)"""
    realization_rate_min: float = 0.92
    realization_rate_max: float = 0.95
    realization_rate_target: float = 0.93

    billable_hours_min: int = 1750
    billable_hours_max: int = 1850
    billable_hours_target: int = 1800

    leverage_ratio_min: float = 2.0
    leverage_ratio_max: float = 3.0
    leverage_ratio_target: float = 2.5

    profit_margin_min: float = 0.35
    profit_margin_max: float = 0.45
    profit_margin_target: float = 0.40

    revenue_per_lawyer_min: int = 500000
    revenue_per_lawyer_max: int = 700000
    revenue_per_lawyer_target: int = 600000


@dataclass
class FirmData:
    """Collected firm data"""
    firm_name: str = ""
    total_attorneys: int = 0
    partner_count: int = 0
    associate_count: int = 0
    of_counsel_count: int = 0
    blended_rate: float = 0.0
    realization_rate: float = 0.0
    billable_hours: int = 0
    gross_revenue: float = 0.0
    revenue_calculated: bool = False
    assumptions: list = None

    def __post_init__(self):
        if self.assumptions is None:
            self.assumptions = []


@dataclass
class CalculatedMetrics:
    """Calculated firm metrics"""
    leverage_ratio: float = 0.0
    revenue_per_lawyer: float = 0.0
    calculated_revenue: float = 0.0
    profit_margin: float = 0.40
    realization_gap_dollars: float = 0.0
    hours_gap_dollars: float = 0.0
    leverage_gap_impact: str = ""
    total_opportunity: float = 0.0


# ============================================================================
# INPUT HELPERS
# ============================================================================

def print_header():
    """Print the tool header"""
    print("\n" + "=" * 70)
    print()
    print("  GABE GROSS CONSULTING")
    print("  Law Firm Profitability Diagnostic Tool")
    print()
    print("=" * 70)
    print()
    print("This tool will guide you through a series of questions to generate")
    print("a comprehensive profitability diagnostic for your law firm.")
    print()
    print("-" * 70)
    print()


def get_input(prompt: str, default: str = "") -> str:
    """Get input with optional default value"""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "

    try:
        value = input(full_prompt).strip()
        return value if value else default
    except (EOFError, KeyboardInterrupt):
        print("\n\nDiagnostic cancelled.")
        sys.exit(0)


def get_integer(prompt: str, min_val: int = None, max_val: int = None,
                context: str = "", default: int = None) -> int:
    """Get and validate an integer input"""
    if context:
        print(f"\n{context}")

    while True:
        default_str = str(default) if default is not None else ""
        value_str = get_input(prompt, default_str)

        if not value_str:
            print("  Please enter a value.")
            continue

        try:
            value = int(value_str.replace(",", ""))
        except ValueError:
            print("  Please enter a valid number.")
            continue

        if min_val is not None and value < min_val:
            print(f"  Value must be at least {min_val:,}.")
            continue
        if max_val is not None and value > max_val:
            print(f"  Value must be at most {max_val:,}.")
            continue

        return value


def get_float(prompt: str, min_val: float = None, max_val: float = None,
              context: str = "", default: float = None, is_currency: bool = False) -> float:
    """Get and validate a float input"""
    if context:
        print(f"\n{context}")

    while True:
        if default is not None:
            if is_currency:
                default_str = f"{default:,.0f}"
            else:
                default_str = str(default)
        else:
            default_str = ""

        value_str = get_input(prompt, default_str)

        if not value_str:
            print("  Please enter a value.")
            continue

        # Clean the input
        value_str = value_str.replace("$", "").replace(",", "").replace("%", "").strip()

        try:
            value = float(value_str)
        except ValueError:
            print("  Please enter a valid number.")
            continue

        if min_val is not None and value < min_val:
            print(f"  Value must be at least {min_val}.")
            continue
        if max_val is not None and value > max_val:
            print(f"  Value must be at most {max_val}.")
            continue

        return value


def get_percentage(prompt: str, min_val: float = 0, max_val: float = 100,
                   context: str = "", default: float = None) -> float:
    """Get and validate a percentage input, return as decimal"""
    if context:
        print(f"\n{context}")

    while True:
        if default is not None:
            default_str = str(default)
        else:
            default_str = ""

        value_str = get_input(prompt, default_str)

        if not value_str:
            print("  Please enter a value.")
            continue

        # Clean the input
        value_str = value_str.replace("%", "").strip()

        try:
            value = float(value_str)
        except ValueError:
            print("  Please enter a valid percentage.")
            continue

        if value < min_val:
            print(f"  Value must be at least {min_val}%.")
            continue
        if value > max_val:
            print(f"  Value must be at most {max_val}%.")
            continue

        return value / 100.0  # Return as decimal


def confirm_yes_no(prompt: str, default: str = "y") -> bool:
    """Get yes/no confirmation"""
    while True:
        if default.lower() == "y":
            choice_str = "[Y/n]"
        else:
            choice_str = "[y/N]"

        value = get_input(f"{prompt} {choice_str}", default)

        if value.lower() in ["y", "yes"]:
            return True
        elif value.lower() in ["n", "no"]:
            return False
        else:
            print("  Please enter 'y' or 'n'.")


# ============================================================================
# DATA COLLECTION
# ============================================================================

def collect_firm_data() -> FirmData:
    """Collect all firm data through conversational prompts"""
    data = FirmData()

    # Firm Name
    print("\nLet's start with some basic information about the firm.")
    data.firm_name = get_input("\nFirm name")
    while not data.firm_name:
        print("  Firm name is required.")
        data.firm_name = get_input("Firm name")

    # Total Attorneys
    data.total_attorneys = get_integer(
        "\nTotal attorney count",
        min_val=20, max_val=150,
        context="This tool is designed for mid-sized firms with 20-150 attorneys."
    )

    # Partner Count
    data.partner_count = get_integer(
        "\nPartner count (equity and non-equity combined)",
        min_val=1, max_val=data.total_attorneys - 1,
        context="Include all partners - both equity and non-equity."
    )

    # Associate Count
    max_associates = data.total_attorneys - data.partner_count
    data.associate_count = get_integer(
        "\nAssociate count",
        min_val=0, max_val=max_associates,
        context=f"How many associates? (Maximum: {max_associates} based on your totals)"
    )

    # Calculate Of Counsel
    data.of_counsel_count = data.total_attorneys - data.partner_count - data.associate_count
    if data.of_counsel_count > 0:
        print(f"\n  Calculated Of Counsel/Counsel count: {data.of_counsel_count}")
        if not confirm_yes_no("  Is this correct?"):
            print("\n  Let's re-verify the attorney counts.")
            print(f"  Total attorneys: {data.total_attorneys}")
            print(f"  Partners: {data.partner_count}")
            print(f"  Associates: {data.associate_count}")
            print(f"  These should add up to total. Please restart if counts are incorrect.")
    else:
        print(f"\n  No Of Counsel/Counsel attorneys calculated (Partners + Associates = Total).")

    # Blended Rate
    data.blended_rate = get_float(
        "\nAverage blended billable rate ($/hour)",
        min_val=100, max_val=2000,
        context="This is the weighted average hourly rate across all timekeepers.\n"
                "For mid-sized firms, this typically ranges from $300-$600/hour.",
        is_currency=True
    )

    # Realization Rate
    data.realization_rate = get_percentage(
        "\nEstimated realization rate (%)",
        min_val=50, max_val=100,
        context="Realization rate is the percentage of billed time you actually collect.\n"
                "For mid-sized firms, this typically ranges from 85-93%.\n"
                "If unsure, 88% is a reasonable industry average.",
        default=88
    )

    # Check if using default and note assumption
    if data.realization_rate == 0.88:
        if confirm_yes_no("\n  Using 88% (industry average). Is this an estimate?"):
            data.assumptions.append("Realization rate based on industry average estimate")

    # Billable Hours
    data.billable_hours = get_integer(
        "\nAverage billable hours per attorney per year",
        min_val=1000, max_val=2500,
        context="This is the average across all attorneys.\n"
                "Mid-sized firm targets are typically 1,750-1,850 hours.\n"
                "If unsure, 1,650 is a reasonable conservative estimate.",
        default=1650
    )

    # Check if using default and note assumption
    if data.billable_hours == 1650:
        if confirm_yes_no("\n  Using 1,650 hours. Is this an estimate?"):
            data.assumptions.append("Billable hours based on conservative industry estimate")

    # Gross Revenue
    print("\n" + "-" * 50)
    print("\nAnnual gross revenue is needed to complete the analysis.")

    calculated_revenue = (data.total_attorneys * data.blended_rate *
                         data.billable_hours * data.realization_rate)

    print(f"\nBased on your inputs, calculated annual revenue would be:")
    print(f"  ${calculated_revenue:,.0f}")
    print(f"  ({data.total_attorneys} attorneys x ${data.blended_rate:,.0f}/hr x "
          f"{data.billable_hours:,} hrs x {data.realization_rate:.0%} realization)")

    if confirm_yes_no("\nDo you know your actual annual gross revenue?", default="n"):
        data.gross_revenue = get_float(
            "Annual gross revenue ($)",
            min_val=1000000,
            is_currency=True
        )
        data.revenue_calculated = False
    else:
        data.gross_revenue = calculated_revenue
        data.revenue_calculated = True
        data.assumptions.append("Gross revenue calculated from input metrics")
        print(f"\n  Using calculated revenue: ${calculated_revenue:,.0f}")

    # Confirm all inputs
    print("\n" + "=" * 70)
    print("\nPLEASE CONFIRM YOUR INPUTS:")
    print("-" * 40)
    print(f"  Firm Name:           {data.firm_name}")
    print(f"  Total Attorneys:     {data.total_attorneys}")
    print(f"  Partners:            {data.partner_count}")
    print(f"  Associates:          {data.associate_count}")
    print(f"  Of Counsel:          {data.of_counsel_count}")
    print(f"  Blended Rate:        ${data.blended_rate:,.0f}/hour")
    print(f"  Realization Rate:    {data.realization_rate:.0%}")
    print(f"  Billable Hours:      {data.billable_hours:,}/year")
    print(f"  Gross Revenue:       ${data.gross_revenue:,.0f}")
    if data.revenue_calculated:
        print("                       (calculated from inputs)")

    if data.assumptions:
        print("\n  Assumptions noted:")
        for assumption in data.assumptions:
            print(f"    - {assumption}")

    print("-" * 40)

    if not confirm_yes_no("\nProceed with analysis?"):
        print("\nRestarting data collection...\n")
        return collect_firm_data()

    return data


# ============================================================================
# CALCULATIONS
# ============================================================================

def calculate_metrics(data: FirmData, benchmarks: Benchmarks) -> CalculatedMetrics:
    """Calculate all metrics and gaps"""
    metrics = CalculatedMetrics()

    # Leverage Ratio
    if data.partner_count > 0:
        metrics.leverage_ratio = data.associate_count / data.partner_count

    # Revenue Per Lawyer
    if data.total_attorneys > 0:
        metrics.revenue_per_lawyer = data.gross_revenue / data.total_attorneys

    # Calculated Revenue (for comparison)
    metrics.calculated_revenue = (data.total_attorneys * data.blended_rate *
                                  data.billable_hours * data.realization_rate)

    # Realization Gap Dollars
    if data.realization_rate < benchmarks.realization_rate_target:
        # Calculate what revenue would be at target realization
        current_billed = data.gross_revenue / data.realization_rate
        target_collected = current_billed * benchmarks.realization_rate_target
        metrics.realization_gap_dollars = target_collected - data.gross_revenue

    # Hours Gap Dollars
    if data.billable_hours < benchmarks.billable_hours_target:
        hours_gap = benchmarks.billable_hours_target - data.billable_hours
        # Additional revenue from additional hours
        metrics.hours_gap_dollars = (data.total_attorneys * hours_gap *
                                     data.blended_rate * data.realization_rate)

    # Leverage Impact (qualitative - harder to quantify directly)
    if metrics.leverage_ratio < benchmarks.leverage_ratio_min:
        metrics.leverage_gap_impact = (
            f"Low leverage ratio ({metrics.leverage_ratio:.1f}) suggests partner capacity "
            f"may be underutilized. Increasing to {benchmarks.leverage_ratio_min:.1f} could "
            f"improve profit margins by 3-5 percentage points."
        )
    elif metrics.leverage_ratio > benchmarks.leverage_ratio_max:
        metrics.leverage_gap_impact = (
            f"High leverage ratio ({metrics.leverage_ratio:.1f}) may indicate partner "
            f"capacity strain. This can lead to quality issues and client attrition."
        )

    # Total Opportunity
    metrics.total_opportunity = metrics.realization_gap_dollars + metrics.hours_gap_dollars

    # Profit Margin Estimate
    # Start at 40% baseline, adjust based on gaps
    metrics.profit_margin = 0.40

    if data.realization_rate < 0.90:
        metrics.profit_margin -= 0.02
    if data.realization_rate < 0.85:
        metrics.profit_margin -= 0.02

    if data.billable_hours < 1700:
        metrics.profit_margin -= 0.02
    if data.billable_hours < 1600:
        metrics.profit_margin -= 0.02

    if metrics.leverage_ratio < 1.5:
        metrics.profit_margin -= 0.02

    if metrics.revenue_per_lawyer < 450000:
        metrics.profit_margin -= 0.02

    return metrics


def get_metric_status(value: float, min_target: float, max_target: float,
                      higher_is_better: bool = True) -> Tuple[str, str]:
    """Determine metric status and return status text and indicator"""
    if higher_is_better:
        if value >= max_target:
            return "Above Target", "[+]"
        elif value >= min_target:
            return "At Target", "[=]"
        elif value >= min_target * 0.9:
            return "Below Target", "[-]"
        else:
            return "Significantly Below Target", "[!]"
    else:
        # For metrics where lower might be concerning (like leverage ratio - both extremes bad)
        if min_target <= value <= max_target:
            return "At Target", "[=]"
        elif value < min_target:
            return "Below Target", "[-]"
        else:
            return "Above Target Range", "[!]"


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(data: FirmData, metrics: CalculatedMetrics,
                    benchmarks: Benchmarks) -> str:
    """Generate the full markdown report"""

    date_str = datetime.now().strftime("%B %d, %Y")

    # Build the report
    lines = []

    # Header
    lines.append("")
    lines.append("# GABE GROSS CONSULTING")
    lines.append("")
    lines.append("## Profitability Diagnostic Report")
    lines.append('### "Capture AI Gains, Don\'t Surrender Them"')
    lines.append("")
    lines.append(f"**Prepared for:** {data.firm_name}")
    lines.append(f"**Date:** {date_str}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")

    summary = generate_executive_summary(data, metrics, benchmarks)
    lines.append(summary)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Scorecard
    lines.append("## Performance Scorecard")
    lines.append("")

    scorecard = generate_scorecard(data, metrics, benchmarks)
    lines.extend(scorecard)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Profitability Gap Analysis
    lines.append("## Profitability Gap Analysis")
    lines.append("")

    gap_analysis = generate_gap_analysis(data, metrics, benchmarks)
    lines.extend(gap_analysis)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Top 3 Recommendations
    lines.append("## Top 3 Recommended Focus Areas")
    lines.append("")

    recommendations = generate_recommendations(data, metrics, benchmarks)
    lines.extend(recommendations)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Next Steps
    lines.append("## Next Steps")
    lines.append("")
    lines.append("This diagnostic is based on estimated inputs. A deeper discovery engagement "
                "with access to actual billing data, timekeeper productivity reports, and "
                "practice area profitability would validate these findings and refine the "
                "opportunity sizing.")
    lines.append("")
    lines.append("To schedule a discovery conversation, contact Gabe Gross at "
                "**gabe@gabegrossconsulting.com**.")
    lines.append("")

    # Assumptions (if any)
    if data.assumptions:
        lines.append("---")
        lines.append("")
        lines.append("### Assumptions")
        lines.append("")
        for assumption in data.assumptions:
            lines.append(f"- {assumption}")
        lines.append("")

    # Footer
    lines.append("---")
    lines.append("")
    lines.append(f"**CONFIDENTIAL:** Prepared exclusively for {data.firm_name}")
    lines.append("")
    lines.append("Gabe Gross Consulting | gabe@gabegrossconsulting.com")
    lines.append("")
    lines.append("*This analysis is based on estimated inputs and industry benchmarks. "
                "Actual results may vary based on firm-specific factors.*")
    lines.append("")

    return "\n".join(lines)


def generate_executive_summary(data: FirmData, metrics: CalculatedMetrics,
                               benchmarks: Benchmarks) -> str:
    """Generate the executive summary paragraph"""

    # Identify the biggest opportunity
    opportunities = []

    if metrics.realization_gap_dollars > 0:
        opportunities.append(("realization", metrics.realization_gap_dollars))
    if metrics.hours_gap_dollars > 0:
        opportunities.append(("hours", metrics.hours_gap_dollars))
    if metrics.leverage_ratio < benchmarks.leverage_ratio_min:
        opportunities.append(("leverage", 100000))  # Placeholder value for sorting

    opportunities.sort(key=lambda x: x[1], reverse=True)

    # Determine overall positioning
    if metrics.revenue_per_lawyer >= benchmarks.revenue_per_lawyer_target:
        positioning = "strong"
    elif metrics.revenue_per_lawyer >= benchmarks.revenue_per_lawyer_min:
        positioning = "competitive"
    else:
        positioning = "developing"

    # Build summary
    summary_parts = []

    summary_parts.append(
        f"{data.firm_name} is a {data.total_attorneys}-attorney firm generating "
        f"**${data.gross_revenue/1000000:.1f}M** in annual revenue, "
        f"with **${metrics.revenue_per_lawyer:,.0f}** in revenue per lawyer."
    )

    if positioning == "strong":
        summary_parts.append(
            "The firm demonstrates strong revenue metrics relative to industry benchmarks."
        )
    elif positioning == "competitive":
        summary_parts.append(
            "The firm operates within competitive industry norms for revenue generation."
        )
    else:
        summary_parts.append(
            "There is meaningful opportunity to improve revenue per lawyer toward industry targets."
        )

    # Lead with biggest opportunity
    if opportunities:
        top_opp = opportunities[0][0]
        if top_opp == "realization":
            summary_parts.append(
                f"The most significant near-term opportunity lies in improving realization rates, "
                f"which could capture approximately **${metrics.realization_gap_dollars:,.0f}** "
                f"in additional collected revenue annually without increasing billable hours."
            )
        elif top_opp == "hours":
            summary_parts.append(
                f"The most significant opportunity lies in improving attorney productivity. "
                f"Raising average billable hours to target levels represents approximately "
                f"**${metrics.hours_gap_dollars:,.0f}** in additional annual revenue."
            )
        elif top_opp == "leverage":
            summary_parts.append(
                f"The firm's leverage ratio of {metrics.leverage_ratio:.1f} associates per partner "
                f"is below the target range of {benchmarks.leverage_ratio_min:.1f}-{benchmarks.leverage_ratio_max:.1f}. "
                f"Optimizing leverage could meaningfully improve partner profitability."
            )

    if metrics.total_opportunity > 0:
        summary_parts.append(
            f"In total, the identified opportunities represent approximately "
            f"**${metrics.total_opportunity:,.0f}** in potential annual improvement."
        )

    return " ".join(summary_parts)


def generate_scorecard(data: FirmData, metrics: CalculatedMetrics,
                       benchmarks: Benchmarks) -> list:
    """Generate the scorecard section"""
    lines = []

    lines.append("| Metric | Current | Target Range | Status | Gap |")
    lines.append("|--------|---------|--------------|--------|-----|")

    # Realization Rate
    status, indicator = get_metric_status(
        data.realization_rate,
        benchmarks.realization_rate_min,
        benchmarks.realization_rate_max
    )
    gap = benchmarks.realization_rate_target - data.realization_rate
    gap_str = f"{gap:+.1%}" if gap != 0 else "-"
    lines.append(
        f"| Realization Rate | {data.realization_rate:.1%} | "
        f"{benchmarks.realization_rate_min:.0%}-{benchmarks.realization_rate_max:.0%} | "
        f"{indicator} {status} | {gap_str} |"
    )

    # Billable Hours
    status, indicator = get_metric_status(
        data.billable_hours,
        benchmarks.billable_hours_min,
        benchmarks.billable_hours_max
    )
    gap = benchmarks.billable_hours_target - data.billable_hours
    gap_str = f"{gap:+,}" if gap != 0 else "-"
    lines.append(
        f"| Billable Hours | {data.billable_hours:,} | "
        f"{benchmarks.billable_hours_min:,}-{benchmarks.billable_hours_max:,} | "
        f"{indicator} {status} | {gap_str} |"
    )

    # Leverage Ratio
    if metrics.leverage_ratio < benchmarks.leverage_ratio_min:
        status = "Below Target"
        indicator = "[-]"
        gap = benchmarks.leverage_ratio_min - metrics.leverage_ratio
        gap_str = f"{gap:+.1f}"
    elif metrics.leverage_ratio > benchmarks.leverage_ratio_max:
        status = "Above Target Range"
        indicator = "[!]"
        gap = metrics.leverage_ratio - benchmarks.leverage_ratio_max
        gap_str = f"+{gap:.1f} over"
    else:
        status = "At Target"
        indicator = "[=]"
        gap_str = "-"
    lines.append(
        f"| Leverage Ratio | {metrics.leverage_ratio:.1f}:1 | "
        f"{benchmarks.leverage_ratio_min:.1f}-{benchmarks.leverage_ratio_max:.1f}:1 | "
        f"{indicator} {status} | {gap_str} |"
    )

    # Revenue Per Lawyer
    status, indicator = get_metric_status(
        metrics.revenue_per_lawyer,
        benchmarks.revenue_per_lawyer_min,
        benchmarks.revenue_per_lawyer_max
    )
    gap = benchmarks.revenue_per_lawyer_target - metrics.revenue_per_lawyer
    gap_str = f"${gap:+,.0f}" if gap != 0 else "-"
    lines.append(
        f"| Revenue/Lawyer | ${metrics.revenue_per_lawyer:,.0f} | "
        f"${benchmarks.revenue_per_lawyer_min/1000:.0f}K-${benchmarks.revenue_per_lawyer_max/1000:.0f}K | "
        f"{indicator} {status} | {gap_str} |"
    )

    # Estimated Profit Margin
    status, indicator = get_metric_status(
        metrics.profit_margin,
        benchmarks.profit_margin_min,
        benchmarks.profit_margin_max
    )
    gap = benchmarks.profit_margin_target - metrics.profit_margin
    gap_str = f"{gap:+.0%}" if abs(gap) > 0.005 else "-"
    lines.append(
        f"| Est. Profit Margin | {metrics.profit_margin:.0%} | "
        f"{benchmarks.profit_margin_min:.0%}-{benchmarks.profit_margin_max:.0%} | "
        f"{indicator} {status} | {gap_str} |"
    )

    return lines


def generate_gap_analysis(data: FirmData, metrics: CalculatedMetrics,
                          benchmarks: Benchmarks) -> list:
    """Generate the gap analysis section"""
    lines = []

    gaps = []

    # Realization Gap
    if metrics.realization_gap_dollars > 0:
        lines.append(f"**Realization Rate Gap**")
        lines.append("")
        lines.append(
            f"Improving realization rate from {data.realization_rate:.0%} to "
            f"{benchmarks.realization_rate_target:.0%} on current billed volume would capture "
            f"approximately **${metrics.realization_gap_dollars:,.0f}** in additional collected "
            f"revenue annually. This represents revenue that is currently being billed but not "
            f"collected due to write-offs, write-downs, and collection failures."
        )
        lines.append("")
        gaps.append(("Realization", metrics.realization_gap_dollars))

    # Hours Gap
    if metrics.hours_gap_dollars > 0:
        hours_gap = benchmarks.billable_hours_target - data.billable_hours
        lines.append(f"**Billable Hours Gap**")
        lines.append("")
        lines.append(
            f"Increasing average billable hours from {data.billable_hours:,} to "
            f"{benchmarks.billable_hours_target:,} per attorney would generate approximately "
            f"**${metrics.hours_gap_dollars:,.0f}** in additional annual revenue. This represents "
            f"an additional {hours_gap:,} hours per attorney across the firm."
        )
        lines.append("")
        gaps.append(("Hours", metrics.hours_gap_dollars))

    # Leverage Gap
    if metrics.leverage_gap_impact:
        lines.append(f"**Leverage Ratio Consideration**")
        lines.append("")
        lines.append(metrics.leverage_gap_impact)
        lines.append("")

    # Revenue Per Lawyer Gap
    if metrics.revenue_per_lawyer < benchmarks.revenue_per_lawyer_min:
        gap = benchmarks.revenue_per_lawyer_target - metrics.revenue_per_lawyer
        total_gap = gap * data.total_attorneys
        lines.append(f"**Revenue Per Lawyer Gap**")
        lines.append("")
        lines.append(
            f"Current revenue per lawyer of ${metrics.revenue_per_lawyer:,.0f} is below the "
            f"target range of ${benchmarks.revenue_per_lawyer_min:,.0f}-${benchmarks.revenue_per_lawyer_max:,.0f}. "
            f"Reaching the midpoint target would require ${gap:,.0f} additional revenue per "
            f"attorney, representing ${total_gap:,.0f} across the firm."
        )
        lines.append("")

    # Total
    lines.append("---")
    lines.append("")
    if metrics.total_opportunity > 0:
        lines.append(
            f"**Total Annual Profitability Improvement Opportunity: "
            f"${metrics.total_opportunity:,.0f}**"
        )
    else:
        lines.append(
            "The firm's metrics are within or above target ranges. Focus should be on "
            "maintaining current performance while exploring strategic growth opportunities."
        )

    return lines


def generate_recommendations(data: FirmData, metrics: CalculatedMetrics,
                             benchmarks: Benchmarks) -> list:
    """Generate top 3 recommendations ranked by impact"""
    lines = []

    # Build recommendation list with impacts
    recs = []

    if metrics.realization_gap_dollars > 0:
        recs.append({
            "title": "Improve Realization Rate",
            "impact": metrics.realization_gap_dollars,
            "gap": f"Current realization of {data.realization_rate:.0%} vs. target of {benchmarks.realization_rate_target:.0%}",
            "why": (
                "Every percentage point of improved realization flows directly to the bottom line "
                "without requiring additional work. Poor realization often stems from inadequate "
                "time capture, billing delays, weak collection practices, or misaligned fee arrangements."
            ),
            "first_step": (
                "Audit your largest 10 write-offs from the past quarter. Categorize by cause "
                "(billing delays, scope disputes, client pushback, collection failures) to identify "
                "the primary driver of lost revenue."
            )
        })

    if metrics.hours_gap_dollars > 0:
        recs.append({
            "title": "Increase Billable Hour Productivity",
            "impact": metrics.hours_gap_dollars,
            "gap": f"Current average of {data.billable_hours:,} hours vs. target of {benchmarks.billable_hours_target:,}",
            "why": (
                "Billable hour shortfalls compound across the entire attorney roster. A 100-hour "
                "gap per attorney in a firm your size represents significant unrealized capacity. "
                "This often reflects administrative burden, inadequate matter flow, or "
                "underutilized timekeepers."
            ),
            "first_step": (
                "Identify your bottom quartile of timekeepers by billable hours. Analyze whether "
                "the gap is due to insufficient matters, excessive non-billable work, or "
                "performance issues requiring targeted intervention."
            )
        })

    if metrics.leverage_ratio < benchmarks.leverage_ratio_min:
        # Estimate impact based on potential margin improvement
        estimated_impact = data.gross_revenue * 0.03  # 3% margin improvement estimate
        recs.append({
            "title": "Optimize Partner-Associate Leverage",
            "impact": estimated_impact,
            "gap": f"Current ratio of {metrics.leverage_ratio:.1f}:1 vs. target of {benchmarks.leverage_ratio_min:.1f}-{benchmarks.leverage_ratio_max:.1f}:1",
            "why": (
                "Low leverage means partners are performing work that could be delegated to "
                "associates at lower cost, reducing overall firm profitability. It may also "
                "indicate challenges in associate recruitment or retention."
            ),
            "first_step": (
                "Review partner time entries for the past month. Identify tasks routinely "
                "performed by partners that could be delegated to associates with appropriate "
                "supervision and training."
            )
        })

    if metrics.revenue_per_lawyer < benchmarks.revenue_per_lawyer_min:
        gap_per_lawyer = benchmarks.revenue_per_lawyer_target - metrics.revenue_per_lawyer
        total_gap = gap_per_lawyer * data.total_attorneys
        recs.append({
            "title": "Improve Revenue Per Lawyer",
            "impact": total_gap,
            "gap": f"${metrics.revenue_per_lawyer:,.0f} vs. target of ${benchmarks.revenue_per_lawyer_target:,.0f}",
            "why": (
                "Revenue per lawyer is a composite metric reflecting rate strength, productivity, "
                "and realization. Below-target performance here suggests systemic issues that "
                "may require examining your rate strategy, client mix, or practice area focus."
            ),
            "first_step": (
                "Segment revenue per lawyer by practice area and seniority level to identify "
                "which segments are underperforming. This will focus improvement efforts on "
                "the areas with the largest gaps."
            )
        })

    # Sort by impact and take top 3
    recs.sort(key=lambda x: x["impact"], reverse=True)
    recs = recs[:3]

    if not recs:
        lines.append(
            "The firm's metrics are within healthy ranges. Consider focusing on strategic "
            "growth initiatives, such as expanding high-margin practice areas, implementing "
            "AI tools to improve efficiency, or exploring alternative fee arrangements that "
            "could further improve profitability."
        )
        return lines

    for i, rec in enumerate(recs, 1):
        lines.append(f"### {i}. {rec['title']}")
        lines.append("")
        lines.append(f"**Potential Annual Impact:** ${rec['impact']:,.0f}")
        lines.append("")
        lines.append(f"**The Gap:** {rec['gap']}")
        lines.append("")
        lines.append(f"**Why It Matters:** {rec['why']}")
        lines.append("")
        lines.append(f"**First Step:** {rec['first_step']}")
        lines.append("")

    return lines


# ============================================================================
# FILE OUTPUT
# ============================================================================

def save_report(data: FirmData, report: str) -> str:
    """Save report to markdown file and return filename"""
    # Clean firm name for filename
    clean_name = re.sub(r'[^\w\s-]', '', data.firm_name)
    clean_name = re.sub(r'[\s]+', '_', clean_name)

    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{clean_name}_Profitability_Diagnostic_{date_str}.md"

    with open(filename, 'w') as f:
        f.write(report)

    return filename


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main entry point"""
    print_header()

    # Collect data
    data = collect_firm_data()

    print("\n" + "=" * 70)
    print("\nGenerating profitability diagnostic report...")
    print()

    # Calculate metrics
    benchmarks = Benchmarks()
    metrics = calculate_metrics(data, benchmarks)

    # Generate report
    report = generate_report(data, metrics, benchmarks)

    # Save to file
    filename = save_report(data, report)
    print(f"Report saved to: {filename}")

    # Offer to display
    print()
    if confirm_yes_no("Would you like to display the full report in the terminal?"):
        print("\n" + "=" * 70)
        print(report)
        print("=" * 70)

    print("\nDiagnostic complete.")
    print()


if __name__ == "__main__":
    main()
