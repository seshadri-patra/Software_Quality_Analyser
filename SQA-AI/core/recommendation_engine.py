"""
Recommendation Engine for SQA-AI
Generates actionable suggestions based on metrics and DDI analysis

Features:
- Rule-based recommendations
- Severity classification
- Priority ranking
- Actionable messages with context

FIXES APPLIED:
- Added volatility rule (was missing)
- Fixed entropy threshold for Shannon entropy (bits scale)
- Added decay rate rule
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Severity(Enum):
    """Severity level of recommendation"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Category(Enum):
    """Category of recommendation"""
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION = "documentation"
    SIZE = "size"
    COUPLING = "coupling"
    COHESION = "cohesion"
    DECAY = "decay"
    ENTROPY = "entropy"
    VOLATILITY = "volatility"
    TESTING = "testing"
    STYLE = "style"


@dataclass
class Recommendation:
    """A single recommendation"""
    id: str
    title: str
    message: str
    severity: Severity
    category: Category
    file_path: str
    
    # Context
    metric_name: str
    metric_value: Any
    threshold: Any
    
    # Actionable details
    action: str
    effort_estimate: str
    impact: str
    
    # Priority score (higher = more urgent)
    priority_score: float = 0.0
    
    # Additional context
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'severity': self.severity.value,
            'category': self.category.value,
            'file_path': self.file_path,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'threshold': self.threshold,
            'action': self.action,
            'effort_estimate': self.effort_estimate,
            'impact': self.impact,
            'priority_score': round(self.priority_score, 2),
            'line_start': self.line_start,
            'line_end': self.line_end,
            'function_name': self.function_name,
            'class_name': self.class_name,
            'created_at': self.created_at.isoformat()
        }
    
    def get_summary(self) -> str:
        """Get one-line summary"""
        return f"[{self.severity.value.upper()}] {self.title} - {self.file_path}"


@dataclass
class Rule:
    """A rule for generating recommendations"""
    id: str
    name: str
    description: str
    category: Category
    
    # Condition
    metric_name: str
    operator: str
    threshold: Any
    
    # Severity mapping
    severity: Severity
    
    # Output templates
    title_template: str
    message_template: str
    action_template: str
    
    # Effort and impact
    effort: str
    impact: str
    
    # Rule weight for priority calculation
    weight: float = 1.0
    
    # Whether rule is enabled
    enabled: bool = True


class RecommendationEngine:
    """
    Generates recommendations based on code metrics and DDI analysis
    """
    
    def __init__(self):
        """Initialize recommendation engine with default rules"""
        self._logger = None
        self._init_logger()
        
        self.rules = self._get_default_rules()
        self._recommendation_counter = 0
    
    def _init_logger(self) -> None:
        """Initialize logger lazily"""
        try:
            from utils.logger import get_logger
            self._logger = get_logger(__name__)
        except ImportError:
            self._logger = None
    
    def _log(self, level: str, message: str) -> None:
        """Log message if logger available"""
        if self._logger:
            getattr(self._logger, level)(message)
    
    def _get_default_rules(self) -> List[Rule]:
        """Define default recommendation rules"""
        return [
            # ============================================
            # COMPLEXITY RULES
            # ============================================
            Rule(
                id="CC001",
                name="High Cyclomatic Complexity",
                description="Function complexity exceeds recommended threshold",
                category=Category.COMPLEXITY,
                metric_name="cyclomatic_complexity",
                operator="gt",
                threshold=20,
                severity=Severity.HIGH,
                title_template="High Cyclomatic Complexity ({value})",
                message_template="The cyclomatic complexity of {value} exceeds the recommended maximum of {threshold}. Complex code is harder to test, understand, and maintain.",
                action_template="Refactor into smaller functions. Extract complex conditions into named methods. Consider using polymorphism instead of conditionals.",
                effort="medium",
                impact="high",
                weight=1.5
            ),
            Rule(
                id="CC002",
                name="Moderate Cyclomatic Complexity",
                description="Function complexity is moderately high",
                category=Category.COMPLEXITY,
                metric_name="cyclomatic_complexity",
                operator="gt",
                threshold=10,
                severity=Severity.MEDIUM,
                title_template="Moderate Cyclomatic Complexity ({value})",
                message_template="The cyclomatic complexity of {value} is above the ideal threshold of {threshold}. Consider simplification.",
                action_template="Review function logic. Look for opportunities to extract helper methods or simplify conditions.",
                effort="low",
                impact="medium",
                weight=1.0
            ),
            Rule(
                id="CC003",
                name="Very High Function Complexity",
                description="Individual function has extreme complexity",
                category=Category.COMPLEXITY,
                metric_name="max_complexity",
                operator="gt",
                threshold=30,
                severity=Severity.CRITICAL,
                title_template="Critical: Function Complexity ({value})",
                message_template="A function has complexity of {value}, which is extremely high. This is a maintenance risk.",
                action_template="Immediately refactor this function. Break it into multiple smaller functions with single responsibilities.",
                effort="high",
                impact="high",
                weight=2.0
            ),
            
            # ============================================
            # MAINTAINABILITY RULES
            # ============================================
            Rule(
                id="MI001",
                name="Poor Maintainability Index",
                description="File has low maintainability score",
                category=Category.MAINTAINABILITY,
                metric_name="maintainability_index",
                operator="lt",
                threshold=40,
                severity=Severity.HIGH,
                title_template="Poor Maintainability Index ({value})",
                message_template="Maintainability index of {value} is below the minimum acceptable threshold of {threshold}. This file will be difficult to maintain.",
                action_template="Reduce complexity, improve documentation, and break down large functions. Consider refactoring or rewriting.",
                effort="high",
                impact="high",
                weight=1.5
            ),
            Rule(
                id="MI002",
                name="Moderate Maintainability",
                description="File maintainability could be improved",
                category=Category.MAINTAINABILITY,
                metric_name="maintainability_index",
                operator="lt",
                threshold=65,
                severity=Severity.MEDIUM,
                title_template="Moderate Maintainability Index ({value})",
                message_template="Maintainability index of {value} is below the ideal threshold of {threshold}.",
                action_template="Add documentation, simplify complex sections, and improve code structure.",
                effort="medium",
                impact="medium",
                weight=1.0
            ),
            
            # ============================================
            # DOCUMENTATION RULES
            # ============================================
            Rule(
                id="DOC001",
                name="Low Comment Density",
                description="File has insufficient documentation",
                category=Category.DOCUMENTATION,
                metric_name="comment_density",
                operator="lt",
                threshold=0.1,
                severity=Severity.MEDIUM,
                title_template="Insufficient Documentation ({value:.1%})",
                message_template="Comment density of {value:.1%} is below the recommended minimum of {threshold:.0%}. Code lacks sufficient documentation.",
                action_template="Add docstrings to functions and classes. Document complex logic with inline comments. Include module-level documentation.",
                effort="low",
                impact="medium",
                weight=0.8
            ),
            Rule(
                id="DOC002",
                name="Very Low Documentation",
                description="File has almost no documentation",
                category=Category.DOCUMENTATION,
                metric_name="comment_density",
                operator="lt",
                threshold=0.05,
                severity=Severity.HIGH,
                title_template="Critical: No Documentation ({value:.1%})",
                message_template="Comment density of {value:.1%} indicates virtually no documentation. This severely impacts maintainability.",
                action_template="Prioritize adding documentation. Start with public APIs, then document complex internal logic.",
                effort="medium",
                impact="high",
                weight=1.2
            ),
            Rule(
                id="DOC003",
                name="Low Docstring Coverage",
                description="Functions lack docstrings",
                category=Category.DOCUMENTATION,
                metric_name="docstring_coverage",
                operator="lt",
                threshold=0.5,
                severity=Severity.MEDIUM,
                title_template="Low Docstring Coverage ({value:.0%})",
                message_template="Only {value:.0%} of functions have docstrings. Target is {threshold:.0%} or higher.",
                action_template="Add docstrings to all public functions. Include parameter descriptions and return values.",
                effort="low",
                impact="medium",
                weight=0.7
            ),
            
            # ============================================
            # SIZE RULES
            # ============================================
            Rule(
                id="SIZE001",
                name="Large File",
                description="File has too many lines of code",
                category=Category.SIZE,
                metric_name="sloc",
                operator="gt",
                threshold=500,
                severity=Severity.MEDIUM,
                title_template="Large File ({value} lines)",
                message_template="File has {value} lines of code, exceeding the recommended maximum of {threshold}. Large files are harder to navigate and maintain.",
                action_template="Split into multiple modules based on functionality. Apply Single Responsibility Principle.",
                effort="high",
                impact="medium",
                weight=0.9
            ),
            Rule(
                id="SIZE002",
                name="Very Large File",
                description="File is excessively large",
                category=Category.SIZE,
                metric_name="sloc",
                operator="gt",
                threshold=1000,
                severity=Severity.HIGH,
                title_template="Very Large File ({value} lines)",
                message_template="File has {value} lines, which is excessively large. This is a significant maintenance burden.",
                action_template="Urgently split this file. Identify cohesive groups of functionality and extract to separate modules.",
                effort="high",
                impact="high",
                weight=1.3
            ),
            Rule(
                id="SIZE003",
                name="Long Function",
                description="Function is too long",
                category=Category.SIZE,
                metric_name="max_function_length",
                operator="gt",
                threshold=50,
                severity=Severity.MEDIUM,
                title_template="Long Function ({value} lines)",
                message_template="A function has {value} lines, exceeding the recommended maximum of {threshold}.",
                action_template="Break down into smaller helper functions. Each function should do one thing well.",
                effort="medium",
                impact="medium",
                weight=0.9
            ),
            Rule(
                id="SIZE004",
                name="Very Long Function",
                description="Function is excessively long",
                category=Category.SIZE,
                metric_name="max_function_length",
                operator="gt",
                threshold=100,
                severity=Severity.HIGH,
                title_template="Very Long Function ({value} lines)",
                message_template="A function has {value} lines, which is extremely long and violates best practices.",
                action_template="Immediately refactor. Extract logical sections into separate functions. Consider using design patterns.",
                effort="high",
                impact="high",
                weight=1.4
            ),
            
            # ============================================
            # COUPLING RULES
            # ============================================
            Rule(
                id="COUP001",
                name="High Import Count",
                description="File has too many imports",
                category=Category.COUPLING,
                metric_name="import_count",
                operator="gt",
                threshold=15,
                severity=Severity.MEDIUM,
                title_template="High Coupling ({value} imports)",
                message_template="File has {value} imports, indicating high coupling. This increases fragility and complexity.",
                action_template="Review dependencies. Consider dependency injection. Look for opportunities to consolidate or abstract.",
                effort="medium",
                impact="medium",
                weight=0.8
            ),
            Rule(
                id="COUP002",
                name="Very High Import Count",
                description="File has excessive imports",
                category=Category.COUPLING,
                metric_name="import_count",
                operator="gt",
                threshold=25,
                severity=Severity.HIGH,
                title_template="Very High Coupling ({value} imports)",
                message_template="File has {value} imports, indicating excessive coupling. This is a design smell.",
                action_template="Major refactoring needed. Consider breaking file apart or introducing facade patterns.",
                effort="high",
                impact="high",
                weight=1.2
            ),
            
            # ============================================
            # DDI/DECAY RULES
            # ============================================
            Rule(
                id="DDI001",
                name="High Decay Risk",
                description="File has high DDI score indicating decay",
                category=Category.DECAY,
                metric_name="ddi_score",
                operator="gt",
                threshold=75,
                severity=Severity.HIGH,
                title_template="High Decay Risk (DDI: {value})",
                message_template="DDI score of {value} indicates significant quality degradation over time. Urgent attention needed.",
                action_template="Review recent changes. Assign clear ownership. Plan dedicated refactoring sprint.",
                effort="high",
                impact="high",
                weight=1.8
            ),
            Rule(
                id="DDI002",
                name="Critical Decay Risk",
                description="File has critical DDI score",
                category=Category.DECAY,
                metric_name="ddi_score",
                operator="gt",
                threshold=90,
                severity=Severity.CRITICAL,
                title_template="Critical Decay Risk (DDI: {value})",
                message_template="DDI score of {value} is critical. This file is highly likely to cause issues soon.",
                action_template="IMMEDIATE ACTION REQUIRED. Stop new development on this file. Dedicate resources to stabilization.",
                effort="high",
                impact="high",
                weight=2.5
            ),
            Rule(
                id="DDI003",
                name="Moderate Decay Risk",
                description="File shows signs of decay",
                category=Category.DECAY,
                metric_name="ddi_score",
                operator="gt",
                threshold=50,
                severity=Severity.MEDIUM,
                title_template="Moderate Decay Risk (DDI: {value})",
                message_template="DDI score of {value} indicates quality is declining. Monitor and plan intervention.",
                action_template="Add to technical debt backlog. Include in upcoming maintenance cycle.",
                effort="medium",
                impact="medium",
                weight=1.0
            ),
            
            # ============================================
            # DECAY RATE RULES (NEW)
            # ============================================
            Rule(
                id="DECAY001",
                name="Rapid Quality Decline",
                description="File quality is declining rapidly",
                category=Category.DECAY,
                metric_name="decay_rate",
                operator="gt",
                threshold=0.5,
                severity=Severity.HIGH,
                title_template="Rapid Quality Decline (Decay Rate: {value:.2f})",
                message_template="Quality decay rate of {value:.2f} indicates rapid deterioration. This file is losing maintainability quickly.",
                action_template="Investigate recent changes. Consider reverting problematic commits. Plan immediate refactoring.",
                effort="high",
                impact="high",
                weight=1.5
            ),
            Rule(
                id="DECAY002",
                name="Quality Declining",
                description="File quality is steadily declining",
                category=Category.DECAY,
                metric_name="decay_rate",
                operator="gt",
                threshold=0.2,
                severity=Severity.MEDIUM,
                title_template="Quality Declining (Decay Rate: {value:.2f})",
                message_template="Quality decay rate of {value:.2f} shows steady decline over time.",
                action_template="Review maintenance practices. Add to refactoring backlog.",
                effort="medium",
                impact="medium",
                weight=1.0
            ),
            
            # ============================================
            # ENTROPY RULES (FIXED for Shannon entropy scale)
            # ============================================
            Rule(
                id="ENT001",
                name="High Contributor Entropy",
                description="Too many contributors without clear ownership",
                category=Category.ENTROPY,
                metric_name="contributor_entropy",
                operator="gt",
                threshold=2.5,  # FIXED: Shannon entropy in bits (was 0.5)
                severity=Severity.HIGH,
                title_template="High Contributor Entropy ({value:.2f} bits)",
                message_template="Contributor entropy of {value:.2f} bits indicates chaotic ownership. Too many people modifying without clear responsibility.",
                action_template="Assign a primary owner. Establish code review requirements. Document architectural decisions.",
                effort="low",
                impact="high",
                weight=1.2
            ),
            Rule(
                id="ENT002",
                name="Moderate Contributor Entropy",
                description="Multiple contributors, ownership unclear",
                category=Category.ENTROPY,
                metric_name="contributor_entropy",
                operator="gt",
                threshold=1.5,  # FIXED: Shannon entropy in bits
                severity=Severity.MEDIUM,
                title_template="Moderate Contributor Entropy ({value:.2f} bits)",
                message_template="Contributor entropy of {value:.2f} bits suggests distributed ownership. Consider assigning a primary maintainer.",
                action_template="Clarify ownership. Ensure knowledge is documented and shared appropriately.",
                effort="low",
                impact="medium",
                weight=0.9
            ),
            Rule(
                id="ENT003",
                name="Many Contributors",
                description="File touched by many different people",
                category=Category.ENTROPY,
                metric_name="contributor_count",
                operator="gt",
                threshold=8,
                severity=Severity.MEDIUM,
                title_template="Many Contributors ({value})",
                message_template="This file has been modified by {value} different contributors. Risk of inconsistent style and hidden assumptions.",
                action_template="Review for consistency. Add comprehensive documentation. Consider assigning primary maintainer.",
                effort="medium",
                impact="medium",
                weight=0.9
            ),
            
            # ============================================
            # VOLATILITY RULES (NEW)
            # ============================================
            Rule(
                id="VOL001",
                name="High Commit Volatility",
                description="Inconsistent maintenance pattern detected",
                category=Category.VOLATILITY,
                metric_name="volatility",
                operator="gt",
                threshold=30,
                severity=Severity.MEDIUM,
                title_template="High Commit Volatility ({value:.1f} days std dev)",
                message_template="Commit volatility of {value:.1f} days standard deviation indicates erratic maintenance patterns.",
                action_template="Establish regular maintenance schedule. Assign clear code ownership. Consider breaking into smaller modules.",
                effort="low",
                impact="medium",
                weight=1.0
            ),
            Rule(
                id="VOL002",
                name="Very High Commit Volatility",
                description="Extremely irregular maintenance pattern",
                category=Category.VOLATILITY,
                metric_name="volatility",
                operator="gt",
                threshold=60,
                severity=Severity.HIGH,
                title_template="Very High Commit Volatility ({value:.1f} days std dev)",
                message_template="Commit volatility of {value:.1f} days indicates very irregular maintenance. This correlates with higher bug rates.",
                action_template="Urgently review maintenance process. Consider dedicated maintenance sprints. Assign ownership.",
                effort="medium",
                impact="high",
                weight=1.3
            ),
            Rule(
                id="VOL003",
                name="Stale File",
                description="File hasn't been updated in a long time",
                category=Category.VOLATILITY,
                metric_name="days_since_last_change",
                operator="gt",
                threshold=180,
                severity=Severity.MEDIUM,
                title_template="Stale File ({value} days since last change)",
                message_template="File hasn't been modified in {value} days. May contain outdated patterns or dependencies.",
                action_template="Review for relevance. Update dependencies. Consider if file is still needed.",
                effort="low",
                impact="medium",
                weight=0.8
            ),
            Rule(
                id="VOL004",
                name="Very Stale File",
                description="File is very outdated",
                category=Category.VOLATILITY,
                metric_name="days_since_last_change",
                operator="gt",
                threshold=365,
                severity=Severity.HIGH,
                title_template="Very Stale File ({value} days since last change)",
                message_template="File hasn't been modified in over a year ({value} days). High risk of outdated code.",
                action_template="Urgent review needed. Check for deprecated dependencies. Consider removal or major refactoring.",
                effort="medium",
                impact="high",
                weight=1.1
            ),
            
            # ============================================
            # HALSTEAD RULES
            # ============================================
            Rule(
                id="HAL001",
                name="High Bug Prediction",
                description="Halstead metrics predict bugs",
                category=Category.COMPLEXITY,
                metric_name="halstead_bugs",
                operator="gt",
                threshold=1.0,
                severity=Severity.HIGH,
                title_template="High Predicted Bugs ({value:.2f})",
                message_template="Halstead analysis predicts {value:.2f} bugs in this code. This is above the acceptable threshold.",
                action_template="Review and test thoroughly. Simplify complex expressions. Break down large functions.",
                effort="medium",
                impact="high",
                weight=1.3
            ),
            Rule(
                id="HAL002",
                name="Very High Bug Prediction",
                description="Halstead metrics predict many bugs",
                category=Category.COMPLEXITY,
                metric_name="halstead_bugs",
                operator="gt",
                threshold=3.0,
                severity=Severity.CRITICAL,
                title_template="Critical: High Predicted Bugs ({value:.2f})",
                message_template="Halstead analysis predicts {value:.2f} bugs. This file needs immediate attention.",
                action_template="Prioritize testing and review. Major refactoring recommended.",
                effort="high",
                impact="high",
                weight=2.0
            )
        ]
    
    def _evaluate_condition(self, value: Any, operator: str, threshold: Any) -> bool:
        """Evaluate a rule condition"""
        if value is None:
            return False
        
        try:
            value = float(value)
            threshold = float(threshold)
        except (TypeError, ValueError):
            return False
        
        if operator == "gt":
            return value > threshold
        elif operator == "lt":
            return value < threshold
        elif operator == "gte":
            return value >= threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "eq":
            return value == threshold
        elif operator == "neq":
            return value != threshold
        
        return False
    
    def _format_template(self, template: str, value: Any, threshold: Any) -> str:
        """Format a template string with values"""
        try:
            return template.format(value=value, threshold=threshold)
        except Exception:
            return template.replace("{value}", str(value)).replace("{threshold}", str(threshold))
    
    def _generate_id(self) -> str:
        """Generate unique recommendation ID"""
        self._recommendation_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"REC-{timestamp}-{self._recommendation_counter:04d}"
    
    def _calculate_priority(
        self, 
        severity: Severity, 
        weight: float,
        impact: str
    ) -> float:
        """Calculate priority score for ranking"""
        severity_scores = {
            Severity.INFO: 10,
            Severity.LOW: 25,
            Severity.MEDIUM: 50,
            Severity.HIGH: 75,
            Severity.CRITICAL: 100
        }
        
        impact_multipliers = {
            "low": 0.8,
            "medium": 1.0,
            "high": 1.2
        }
        
        base_score = severity_scores.get(severity, 50)
        impact_mult = impact_multipliers.get(impact, 1.0)
        
        return base_score * weight * impact_mult
    
    def analyze_file(
        self,
        file_path: str,
        metrics: Dict[str, Any],
        ddi_result: Optional[Any] = None,
        functions: Optional[List[Dict]] = None,
        classes: Optional[List[Dict]] = None
    ) -> List[Recommendation]:
        """
        Analyze a file and generate recommendations
        
        Args:
            file_path: Path to the file
            metrics: File metrics dictionary
            ddi_result: Optional DDIResult object
            functions: Optional list of function metrics
            classes: Optional list of class metrics
        
        Returns:
            List of Recommendation objects
        """
        recommendations = []
        
        # Add DDI metrics if available
        if ddi_result:
            if hasattr(ddi_result, 'ddi_score'):
                metrics['ddi_score'] = ddi_result.ddi_score
                metrics['contributor_entropy'] = ddi_result.contributor_entropy
                metrics['contributor_count'] = ddi_result.contributor_count
                metrics['volatility'] = ddi_result.volatility
                metrics['decay_rate'] = ddi_result.decay_rate
                metrics['days_since_last_change'] = ddi_result.days_since_last_change
            elif isinstance(ddi_result, dict):
                metrics['ddi_score'] = ddi_result.get('ddi_score', 0)
                metrics['contributor_entropy'] = ddi_result.get('contributor_entropy', 0)
                metrics['contributor_count'] = ddi_result.get('contributor_count', 0)
                metrics['volatility'] = ddi_result.get('volatility', 0)
                metrics['decay_rate'] = ddi_result.get('decay_rate', 0)
                metrics['days_since_last_change'] = ddi_result.get('days_since_last_change', 0)
        
        # Evaluate each rule
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            value = metrics.get(rule.metric_name)
            
            if self._evaluate_condition(value, rule.operator, rule.threshold):
                priority = self._calculate_priority(rule.severity, rule.weight, rule.impact)
                
                recommendation = Recommendation(
                    id=self._generate_id(),
                    title=self._format_template(rule.title_template, value, rule.threshold),
                    message=self._format_template(rule.message_template, value, rule.threshold),
                    severity=rule.severity,
                    category=rule.category,
                    file_path=file_path,
                    metric_name=rule.metric_name,
                    metric_value=value,
                    threshold=rule.threshold,
                    action=self._format_template(rule.action_template, value, rule.threshold),
                    effort_estimate=rule.effort,
                    impact=rule.impact,
                    priority_score=priority
                )
                
                recommendations.append(recommendation)
        
        # Analyze individual functions if provided
        if functions:
            for func in functions:
                func_recs = self._analyze_function(file_path, func)
                recommendations.extend(func_recs)
        
        # Analyze individual classes if provided
        if classes:
            for cls in classes:
                cls_recs = self._analyze_class(file_path, cls)
                recommendations.extend(cls_recs)
        
        # Sort by priority (highest first)
        recommendations.sort(key=lambda r: r.priority_score, reverse=True)
        
        self._log('debug', f"Generated {len(recommendations)} recommendations for {file_path}")
        
        return recommendations
    
    def _analyze_function(self, file_path: str, func: Dict) -> List[Recommendation]:
        """Analyze a single function and generate recommendations"""
        recommendations = []
        
        func_name = func.get('name', 'unknown')
        complexity = func.get('complexity', 0)
        lines = func.get('lines', 0)
        has_docstring = func.get('has_docstring', False)
        parameters = func.get('parameters', 0)
        line_start = func.get('line_start')
        line_end = func.get('line_end')
        
        # High complexity function
        if complexity > 15:
            severity = Severity.HIGH if complexity > 25 else Severity.MEDIUM
            recommendations.append(Recommendation(
                id=self._generate_id(),
                title=f"Complex function: {func_name}",
                message=f"Function '{func_name}' has complexity of {complexity}, which is too high.",
                severity=severity,
                category=Category.COMPLEXITY,
                file_path=file_path,
                metric_name="function_complexity",
                metric_value=complexity,
                threshold=15,
                action="Break down into smaller, focused functions. Extract complex conditions.",
                effort_estimate="medium",
                impact="high",
                priority_score=70 if severity == Severity.HIGH else 50,
                function_name=func_name,
                line_start=line_start,
                line_end=line_end
            ))
        
        # Long function
        if lines > 40:
            severity = Severity.HIGH if lines > 80 else Severity.MEDIUM
            recommendations.append(Recommendation(
                id=self._generate_id(),
                title=f"Long function: {func_name}",
                message=f"Function '{func_name}' has {lines} lines, exceeding best practices.",
                severity=severity,
                category=Category.SIZE,
                file_path=file_path,
                metric_name="function_length",
                metric_value=lines,
                threshold=40,
                action="Break down into smaller helper functions. Each function should do one thing well.",
                effort_estimate="medium",
                impact="medium",
                priority_score=60 if severity == Severity.HIGH else 40,
                function_name=func_name,
                line_start=line_start,
                line_end=line_end
            ))
        
        # Missing docstring
        if not has_docstring and not func_name.startswith('_'):
            recommendations.append(Recommendation(
                id=self._generate_id(),
                title=f"Missing docstring: {func_name}",
                message=f"Public function '{func_name}' lacks a docstring.",
                severity=Severity.LOW,
                category=Category.DOCUMENTATION,
                file_path=file_path,
                metric_name="has_docstring",
                metric_value=False,
                threshold=True,
                action="Add a docstring describing the function's purpose, parameters, and return value.",
                effort_estimate="low",
                impact="low",
                priority_score=20,
                function_name=func_name,
                line_start=line_start,
                line_end=line_end
            ))
        
        # Too many parameters
        if parameters > 5:
            severity = Severity.MEDIUM if parameters <= 8 else Severity.HIGH
            recommendations.append(Recommendation(
                id=self._generate_id(),
                title=f"Too many parameters: {func_name}",
                message=f"Function '{func_name}' has {parameters} parameters. Consider refactoring.",
                severity=severity,
                category=Category.COMPLEXITY,
                file_path=file_path,
                metric_name="parameters",
                metric_value=parameters,
                threshold=5,
                action="Group related parameters into a class or dataclass. Consider using **kwargs for optional params.",
                effort_estimate="medium",
                impact="medium",
                priority_score=45,
                function_name=func_name,
                line_start=line_start,
                line_end=line_end
            ))
        
        return recommendations
    
    def _analyze_class(self, file_path: str, cls: Dict) -> List[Recommendation]:
        """Analyze a single class and generate recommendations"""
        recommendations = []
        
        class_name = cls.get('name', 'unknown')
        method_count = cls.get('method_count', 0)
        wmc = cls.get('wmc', 0)  # Weighted Methods per Class
        attributes = cls.get('attributes', 0)
        has_docstring = cls.get('has_docstring', False)
        line_start = cls.get('line_start')
        line_end = cls.get('line_end')
        
        # High WMC (Weighted Methods per Class)
        if wmc > 50:
            severity = Severity.HIGH if wmc > 100 else Severity.MEDIUM
            recommendations.append(Recommendation(
                id=self._generate_id(),
                title=f"High class complexity: {class_name}",
                message=f"Class '{class_name}' has WMC (Weighted Methods per Class) of {wmc}. This indicates high complexity.",
                severity=severity,
                category=Category.COMPLEXITY,
                file_path=file_path,
                metric_name="wmc",
                metric_value=wmc,
                threshold=50,
                action="Consider splitting into smaller classes. Apply Single Responsibility Principle.",
                effort_estimate="high",
                impact="high",
                priority_score=75 if severity == Severity.HIGH else 55,
                class_name=class_name,
                line_start=line_start,
                line_end=line_end
            ))
        
        # Too many methods
        if method_count > 15:
            severity = Severity.MEDIUM if method_count <= 25 else Severity.HIGH
            recommendations.append(Recommendation(
                id=self._generate_id(),
                title=f"Too many methods: {class_name}",
                message=f"Class '{class_name}' has {method_count} methods. Consider splitting responsibilities.",
                severity=severity,
                category=Category.SIZE,
                file_path=file_path,
                metric_name="method_count",
                metric_value=method_count,
                threshold=15,
                action="Extract related methods into separate classes. Apply composition over inheritance.",
                effort_estimate="high",
                impact="medium",
                priority_score=50,
                class_name=class_name,
                line_start=line_start,
                line_end=line_end
            ))
        
        # Missing class docstring
        if not has_docstring:
            recommendations.append(Recommendation(
                id=self._generate_id(),
                title=f"Missing class docstring: {class_name}",
                message=f"Class '{class_name}' lacks a docstring.",
                severity=Severity.LOW,
                category=Category.DOCUMENTATION,
                file_path=file_path,
                metric_name="has_docstring",
                metric_value=False,
                threshold=True,
                action="Add a docstring describing the class's purpose, attributes, and usage.",
                effort_estimate="low",
                impact="low",
                priority_score=15,
                class_name=class_name,
                line_start=line_start,
                line_end=line_end
            ))
        
        return recommendations
    
    def analyze_project(
        self,
        file_metrics_list: List[Dict[str, Any]],
        ddi_results: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze entire project and generate summary
        
        Args:
            file_metrics_list: List of file metrics dictionaries
            ddi_results: Optional list of DDI results
        
        Returns:
            Project analysis summary with all recommendations
        """
        all_recommendations = []
        file_summaries = []
        
        for i, metrics in enumerate(file_metrics_list):
            file_path = metrics.get('file_path', f'file_{i}')
            
            # Get corresponding DDI result if available
            ddi_result = None
            if ddi_results and i < len(ddi_results):
                ddi_result = ddi_results[i]
            
            # Get functions and classes if available
            functions = metrics.get('functions', [])
            classes = metrics.get('classes', [])
            
            # Analyze file
            recommendations = self.analyze_file(
                file_path, metrics, ddi_result, functions, classes
            )
            
            all_recommendations.extend(recommendations)
            
            file_summaries.append({
                'file_path': file_path,
                'recommendation_count': len(recommendations),
                'critical_count': sum(1 for r in recommendations if r.severity == Severity.CRITICAL),
                'high_count': sum(1 for r in recommendations if r.severity == Severity.HIGH)
            })
        
        # Sort all recommendations by priority
        all_recommendations.sort(key=lambda r: r.priority_score, reverse=True)
        
        # Generate summary statistics
        summary = self._generate_project_summary(all_recommendations, file_summaries)
        
        return {
            'summary': summary,
            'recommendations': [r.to_dict() for r in all_recommendations],
            'file_summaries': file_summaries,
            'top_priority': [r.to_dict() for r in all_recommendations[:10]]
        }
    
    def _generate_project_summary(
        self,
        recommendations: List[Recommendation],
        file_summaries: List[Dict]
    ) -> Dict[str, Any]:
        """Generate project-level summary"""
        if not recommendations:
            return {
                'total_recommendations': 0,
                'health_score': 100,
                'status': 'excellent'
            }
        
        severity_counts = {
            'critical': sum(1 for r in recommendations if r.severity == Severity.CRITICAL),
            'high': sum(1 for r in recommendations if r.severity == Severity.HIGH),
            'medium': sum(1 for r in recommendations if r.severity == Severity.MEDIUM),
            'low': sum(1 for r in recommendations if r.severity == Severity.LOW),
            'info': sum(1 for r in recommendations if r.severity == Severity.INFO)
        }
        
        category_counts = {}
        for r in recommendations:
            cat = r.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Calculate health score (0-100)
        health_score = 100
        health_score -= severity_counts['critical'] * 15
        health_score -= severity_counts['high'] * 8
        health_score -= severity_counts['medium'] * 3
        health_score -= severity_counts['low'] * 1
        health_score = max(0, health_score)
        
        # Determine status
        if health_score >= 80:
            status = 'good'
        elif health_score >= 60:
            status = 'moderate'
        elif health_score >= 40:
            status = 'concerning'
        else:
            status = 'critical'
        
        # Files needing attention
        files_needing_attention = [
            f['file_path'] for f in file_summaries
            if f['critical_count'] > 0 or f['high_count'] > 2
        ]
        
        return {
            'total_recommendations': len(recommendations),
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
            'health_score': health_score,
            'status': status,
            'files_analyzed': len(file_summaries),
            'files_needing_attention': files_needing_attention,
            'top_categories': sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        }
    
    def add_rule(self, rule: Rule) -> None:
        """Add a custom rule"""
        self.rules.append(rule)
        self._log('info', f"Added rule: {rule.id} - {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a rule by ID"""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                del self.rules[i]
                self._log('info', f"Removed rule: {rule_id}")
                return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule by ID"""
        for rule in self.rules:
            if rule.id == rule_id:
                rule.enabled = True
                return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule by ID"""
        for rule in self.rules:
            if rule.id == rule_id:
                rule.enabled = False
                return True
        return False
    
    def get_rules_by_category(self, category: Category) -> List[Rule]:
        """Get all rules in a category"""
        return [r for r in self.rules if r.category == category]
    
    def get_enabled_rules(self) -> List[Rule]:
        """Get all enabled rules"""
        return [r for r in self.rules if r.enabled]
    
    def __repr__(self) -> str:
        enabled = sum(1 for r in self.rules if r.enabled)
        return f"RecommendationEngine(rules={len(self.rules)}, enabled={enabled})"


# Convenience functions
def analyze_file(file_path: str, metrics: Dict[str, Any]) -> List[Recommendation]:
    """Quick analyze a file"""
    engine = RecommendationEngine()
    return engine.analyze_file(file_path, metrics)


def get_recommendations(metrics: Dict[str, Any]) -> List[Dict]:
    """Quick get recommendations as dictionaries"""
    engine = RecommendationEngine()
    recs = engine.analyze_file(metrics.get('file_path', 'unknown'), metrics)
    return [r.to_dict() for r in recs]
