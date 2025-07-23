"""
CFA Level III topic configuration and weights
"""

# CFA Level III Topic Weights
TOPIC_WEIGHTS = {
    "Asset Allocation": {"min": 15, "max": 20, "target": 17.5},
    "Portfolio Construction": {"min": 15, "max": 20, "target": 17.5},
    "Performance Management": {"min": 5, "max": 10, "target": 7.5},
    "Derivatives & Risk Management": {"min": 10, "max": 15, "target": 12.5},
    "Ethics & Professional Standards": {"min": 10, "max": 15, "target": 12.5},
    "Portfolio Management Pathway": {"min": 30, "max": 35, "target": 32.5}
}

# Topic keywords for classification
TOPIC_KEYWORDS = {
    "Asset Allocation": [
        "asset allocation", "strategic allocation", "tactical allocation", "mean-variance optimization",
        "efficient frontier", "risk budgeting", "liability-driven investing", "ALM", "asset-liability matching",
        "rebalancing", "portfolio optimization", "capital market expectations", "monte carlo simulation"
    ],
    "Portfolio Construction": [
        "portfolio construction", "factor investing", "smart beta", "alternative investments",
        "private equity", "hedge funds", "real estate", "commodities", "currency management",
        "overlay strategies", "completion portfolios", "core-satellite", "barbell strategy"
    ],
    "Performance Management": [
        "performance measurement", "performance attribution", "GIPS", "benchmarking",
        "risk-adjusted returns", "sharpe ratio", "information ratio", "tracking error",
        "alpha", "beta", "performance evaluation", "attribution analysis", "appraisal ratio"
    ],
    "Derivatives & Risk Management": [
        "derivatives", "options", "futures", "swaps", "forwards", "risk management",
        "hedging", "VaR", "value at risk", "credit risk", "market risk", "operational risk",
        "stress testing", "scenario analysis", "tail risk", "downside protection"
    ],
    "Ethics & Professional Standards": [
        "ethics", "professional standards", "code of ethics", "standards of professional conduct",
        "fiduciary duty", "conflicts of interest", "material nonpublic information", "fair dealing",
        "suitability", "performance presentation", "compliance", "investment management process"
    ],
    "Portfolio Management Pathway": [
        "institutional portfolio management", "individual portfolio management", "wealth management",
        "pension funds", "endowments", "foundations", "insurance companies", "banks",
        "sovereign wealth funds", "family offices", "high net worth", "retirement planning",
        "estate planning", "tax considerations", "behavioral finance", "client management"
    ]
}

# Question types and formats
QUESTION_TYPES = {
    "AM": {
        "type": "constructed_response",
        "count": {"min": 3, "max": 5},
        "time_minutes": 180,
        "format": "essay_with_calculations",
        "answer_format": "bullet_points_with_rubric"
    },
    "PM": {
        "type": "item_set",
        "count": {"min": 4, "max": 6},
        "time_minutes": 180,
        "questions_per_set": 3,
        "format": "multiple_choice",
        "answer_format": "detailed_explanations"
    }
}

# Difficulty levels
DIFFICULTY_LEVELS = {
    "Level_1": {"weight": 0.2, "description": "Basic recall and understanding"},
    "Level_2": {"weight": 0.5, "description": "Application and analysis"},
    "Level_3": {"weight": 0.3, "description": "Synthesis and evaluation"}
}
