"""
agents — AgriIntel Intelligence Swarm
======================================
This package contains all eight production agents that power the
AgriIntel platform.  Each agent is a self-contained, stateless class
with a clearly defined role in the intelligence pipeline.

Agent roster
------------
1.  SentimentAgent         (sentiment_analysis)   — NLP sentiment scorer
2.  ForecastingAgent       (forecast_execution)   — RACE ensemble price forecaster
3.  AnomalyDetectionEngine (shock_monitoring)     — real-time shock detector
4.  MarketRiskEngine       (risk_scoring)         — 0-100 composite risk scorer
5.  DecisionAgent          (decision_support)     — Buy / Sell / Hold signal generator
6.  DataReliabilityAgent   (data_reliability)     — ETL data quality gate
7.  IntelligenceAgent      (intelligence_core)    — consultant and scenario engine
8.  PerformanceMonitor     (performance_monitor)  — model accuracy tracker

Usage
-----
    from agents.forecast_execution import ForecastingAgent
    from agents.risk_scoring import MarketRiskEngine
"""
