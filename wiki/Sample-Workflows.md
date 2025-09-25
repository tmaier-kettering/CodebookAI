# Sample Workflows

Complete, step-by-step examples of real-world CodebookAI projects. These workflows demonstrate best practices in action and provide templates you can adapt for your own research.

## 🎯 Workflow Overview

Each workflow follows the same general structure:
1. **Project Setup**: Define goals and prepare data
2. **Label Development**: Create and test classification scheme
3. **Small-Scale Validation**: Test approach with subset of data
4. **Large-Scale Processing**: Process full dataset efficiently
5. **Quality Assurance**: Validate results and measure reliability
6. **Analysis and Reporting**: Extract insights and document findings

---

## 📊 Workflow 1: Customer Feedback Analysis

### Project Context
**Scenario**: E-commerce company wants to analyze 5,000 customer reviews to understand sentiment and identify key issues.

**Goals**:
- Classify sentiment (positive, negative, neutral)
- Identify main complaint categories
- Quantify customer satisfaction trends
- Prioritize improvement areas

### Step 1: Project Setup

#### Data Preparation
**Original Data** (`customer_reviews.csv`):
```csv
review_id,customer_id,product_id,review_text,rating,date
1,C001,P123,"Great product, fast shipping!",5,2024-01-15
2,C002,P124,"Poor quality, broke after one week",1,2024-01-16
3,C003,P123,"Works fine, nothing special",3,2024-01-17
```

**Cleaned for Processing**:
```csv
text,id,rating,date
"Great product, fast shipping!",1,5,2024-01-15
"Poor quality, broke after one week",2,1,2024-01-16
"Works fine, nothing special",3,3,2024-01-17
```

#### Label Set Design
**Sentiment Labels** (`sentiment_labels.csv`):
```
positive
negative
neutral
```

**Issue Category Labels** (`issue_labels.csv`):
```
product_quality
shipping_delivery
customer_service
pricing_value
website_usability
no_specific_issue
```

### Step 2: Small-Scale Testing

#### Phase 1: Test Sentiment Classification (100 reviews)
1. **Use Live Processing**: LLM Tools → Live Methods → Single Label Classification
2. **Import Labels**: Select `sentiment_labels.csv`
3. **Import Text**: Select sample of 100 reviews
4. **Processing Time**: ~5 minutes
5. **Results Review**: Manual check of 20 random classifications

**Sample Results**:
```csv
id,quote,label
1,"Great product, fast shipping!",positive
2,"Poor quality, broke after one week",negative
3,"Works fine, nothing special",neutral
```

#### Phase 2: Test Issue Classification (Same 100 reviews)
1. **Multi-Label Processing**: LLM Tools → Live Methods → Multi-Label Classification
2. **Import Issue Labels**: Select `issue_labels.csv`
3. **Import Same Text**: Same 100 review sample
4. **Review Results**: Check for logical label combinations

**Sample Results**:
```csv
id,quote,label
1,"Great product, fast shipping!","['no_specific_issue']"
2,"Poor quality, broke after one week","['product_quality']"
3,"Slow shipping, but good product","['shipping_delivery']"
```

### Step 3: Validation and Refinement

#### Human Validation
1. **Random Sample**: Select 50 reviews from test set
2. **Expert Classification**: Have customer service manager classify manually
3. **Calculate Agreement**: Use Data Analysis → Reliability Statistics

**Reliability Results**:
- **Sentiment**: 87% agreement, κ = 0.78 (substantial agreement)
- **Issues**: 82% agreement, κ = 0.71 (substantial agreement)

#### Label Refinement
Based on disagreements, refine labels:
```
Original: product_quality
Refined: product_defect, product_durability, product_functionality

Original: shipping_delivery  
Refined: shipping_speed, shipping_damage, delivery_issues
```

### Step 4: Large-Scale Processing

#### Batch Processing Setup
1. **Split Data**: Divide 5,000 reviews into 5 batches of 1,000 each
2. **Batch Method**: LLM Tools → Batch Methods → Single Label Classification
3. **Model Choice**: gpt-4o-mini for cost efficiency
4. **Submit Jobs**: Process sentiment and issues separately

#### Batch Processing Timeline
- **Day 1**: Submit sentiment classification batches
- **Day 2**: Submit issue classification batches  
- **Day 3-4**: Monitor progress, retrieve results
- **Day 5**: Combine and validate results

#### Cost Analysis
```
Sentiment Classification:
- 5,000 reviews × ~30 tokens each = 150,000 tokens
- Batch processing discount (~50% off)
- Estimated cost: ~$0.15 (gpt-4o-mini)

Issue Classification:
- Same token count, similar cost
- Total project cost: ~$0.30
```

### Step 5: Quality Assurance

#### Statistical Validation
1. **Random Sample**: 200 reviews across all batches
2. **Manual Review**: Customer service team validates
3. **Reliability Analysis**: Compare batch results with manual coding

**Final Quality Metrics**:
- **Sentiment**: 89% accuracy, κ = 0.82
- **Issues**: 84% accuracy, κ = 0.76
- **Processing Success**: 99.2% of reviews successfully classified

#### Error Analysis
**Common Errors Found**:
- Sarcastic reviews sometimes misclassified as positive
- Multi-issue reviews sometimes missed secondary issues
- Very short reviews (<10 words) less reliable

### Step 6: Analysis and Reporting

#### Key Findings
**Sentiment Distribution**:
- Positive: 62% (3,100 reviews)
- Negative: 23% (1,150 reviews)  
- Neutral: 15% (750 reviews)

**Top Issues**:
1. Product Quality: 28% of negative reviews
2. Shipping Speed: 21% of negative reviews
3. Customer Service: 18% of negative reviews
4. Pricing: 15% of negative reviews

#### Business Recommendations
1. **Product Quality**: Investigate most-mentioned defects
2. **Shipping**: Consider faster shipping options
3. **Customer Service**: Additional training for support team
4. **Pricing**: Review pricing strategy for value perception

#### Export for Further Analysis
```csv
review_id,text,sentiment,issues,confidence,processing_date
1,"Great product!",positive,"['no_specific_issue']",high,2024-01-20
2,"Broke quickly",negative,"['product_defect']",high,2024-01-20
```

---

## 🎓 Workflow 2: Academic Research - Interview Analysis

### Project Context
**Scenario**: Education researcher analyzing 200 teacher interviews about remote learning challenges during COVID-19.

**Goals**:
- Identify main themes in teacher experiences
- Categorize types of challenges mentioned
- Analyze emotional responses to remote teaching
- Support qualitative research with quantitative analysis

### Step 1: Research Design

#### Data Preparation
**Interview Transcript Processing**:
1. **Extract Segments**: Break interviews into meaningful chunks (200-400 words)
2. **Remove Identifiers**: Anonymize all personal information
3. **Standard Format**: Convert to consistent CSV structure

**Prepared Data** (`interview_segments.csv`):
```csv
segment_id,teacher_id,question_topic,text,interview_date
001,T001,challenges,"The biggest challenge was maintaining student engagement through screens...",2020-05-15
002,T001,technology,"Our school provided laptops but many students had connectivity issues...",2020-05-15
```

#### Theoretical Framework
**Thematic Categories** (based on literature review):
```csv
label
technology_challenges
student_engagement
work_life_balance
professional_development
administrative_support
parent_communication
assessment_difficulties
emotional_wellbeing
```

### Step 2: Pilot Testing

#### Small Sample Analysis (30 segments)
1. **Manual Coding**: Research team codes 30 segments manually
2. **AI Testing**: Same segments processed with Live Multi-Label
3. **Comparison**: Identify discrepancies and refine approach

**Inter-rater Reliability (Human Coders)**:
- Coder A vs Coder B: κ = 0.68
- Discussion and refinement needed

#### Label Refinement Process
**Original Problem**: "technology_challenges" too broad
**Solution**: Split into specific categories:
```
technology_access        # Hardware/software availability
technology_skills        # Teacher technical competency  
technology_support      # IT support availability
platform_issues         # Specific software problems
```

### Step 3: Validation Study

#### Ground Truth Development
1. **Expert Panel**: 3 education researchers
2. **Sample Size**: 100 interview segments  
3. **Consensus Method**: Discuss disagreements until consensus
4. **Final Labels**: Authoritative classification for validation

#### AI vs Expert Comparison
**Live Processing Results**:
- **Overall Agreement**: 78% (need improvement)
- **Problematic Categories**: Emotional themes harder to detect
- **Strong Performance**: Technology and administrative themes

#### Model Optimization
**Testing Different Models**:
- gpt-4o-mini: 78% accuracy, very fast, low cost
- gpt-4o: 85% accuracy, moderate cost
- gpt-4-turbo: 89% accuracy, high cost

**Decision**: Use gpt-4o for balance of accuracy and cost

### Step 4: Full Dataset Processing

#### Batch Processing Strategy
```
Total: 800 interview segments
Batch Size: 200 segments each
Number of Batches: 4
Processing Method: Multi-label classification
Model: gpt-4o
```

#### Timeline and Monitoring
- **Day 1**: Submit all 4 batches
- **Day 2-3**: Monitor batch progress
- **Day 4**: All batches completed
- **Day 5**: Download and process results

### Step 5: Quality Control

#### Systematic Validation
1. **Stratified Sample**: 10% from each thematic category
2. **Blind Review**: Researchers validate without seeing AI labels
3. **Statistical Analysis**: Calculate final reliability metrics

**Final Performance Metrics**:
- **Accuracy**: 86.5% overall
- **Inter-rater Reliability**: κ = 0.81 (almost perfect)
- **Category Performance**: 
  - Technology themes: 92% accuracy
  - Emotional themes: 79% accuracy
  - Administrative themes: 88% accuracy

### Step 6: Research Analysis

#### Quantitative Findings
**Theme Prevalence** (n=800 segments):
1. Technology Challenges: 67% of segments
2. Student Engagement: 54% of segments  
3. Work-Life Balance: 41% of segments
4. Emotional Wellbeing: 38% of segments
5. Administrative Support: 29% of segments

#### Qualitative Integration
**Mixed Methods Approach**:
1. **AI Classification** provides broad patterns
2. **Human Analysis** explores nuanced examples
3. **Correlogram Visualization** shows theme relationships
4. **Case Studies** dive deep into specific patterns

#### Academic Output
```
Research Paper Structure:
1. Literature Review (manual analysis)
2. Methodology (CodebookAI + human validation)
3. Quantitative Results (AI classification patterns)
4. Qualitative Analysis (selected examples)
5. Discussion (integrated insights)
6. Limitations (AI accuracy bounds)
```

---

## 💼 Workflow 3: Content Moderation at Scale

### Project Context
**Scenario**: Social media platform needs to classify 50,000 user comments for content moderation.

**Goals**:
- Identify potentially harmful content
- Categorize types of policy violations
- Prioritize human moderator review
- Improve automated moderation systems

### Step 1: Policy Framework

#### Content Categories
```csv
label
safe_content
spam_promotional
harassment_bullying
hate_speech
misinformation
adult_content
violence_threats
self_harm_content
intellectual_property
privacy_violation
```

#### Risk-Based Approach
**Priority Levels**:
- **High Priority**: hate_speech, violence_threats, self_harm_content
- **Medium Priority**: harassment_bullying, misinformation  
- **Low Priority**: spam_promotional, adult_content
- **Review Only**: safe_content, intellectual_property

### Step 2: Careful Validation

#### Ethical Considerations
1. **Human Welfare**: Minimize exposure to harmful content
2. **Accuracy Requirements**: High precision needed (minimize false positives)
3. **Bias Detection**: Test for demographic and cultural biases
4. **Legal Compliance**: Ensure approach meets regulatory requirements

#### Validation Dataset
1. **Expert Team**: Content moderation specialists
2. **Sample Size**: 1,000 carefully selected comments
3. **Balanced Sample**: Equal representation across categories
4. **Multiple Reviewers**: 3 reviewers per comment for consensus

### Step 3: Multi-Stage Processing

#### Stage 1: High-Confidence Detection
**Batch Processing** (gpt-4-turbo for accuracy):
- Process all 50,000 comments
- Flag high-confidence violations
- Generate confidence scores

#### Stage 2: Human Review Integration
**Workflow**:
```
AI Classification → Confidence Assessment → Routing Decision

High Confidence Violations → Immediate Action
Medium Confidence → Human Review Queue  
Low Confidence → Community Guidelines Notice
Safe Content → No Action
```

#### Stage 3: Quality Monitoring
**Continuous Validation**:
- Daily sample validation (100 comments)
- Weekly bias assessment
- Monthly model performance review
- Quarterly policy alignment check

### Step 4: Results and Actions

#### Processing Outcomes
**50,000 Comments Processed**:
- Safe Content: 82% (41,000 comments)
- Policy Violations: 12% (6,000 comments)
- Uncertain/Review: 6% (3,000 comments)

**Action Distribution**:
- Automated Actions: 85% of violations
- Human Review Queue: 15% of violations
- Appeal Process: 2% of actions

#### Performance Metrics
- **Processing Speed**: 50,000 comments in 6 hours
- **Human Review Reduction**: 70% fewer items for manual review
- **Accuracy**: 94% agreement with expert moderators
- **False Positive Rate**: 3% (critical for user experience)

---

## 🏥 Workflow 4: Healthcare Feedback Analysis

### Project Context
**Scenario**: Hospital system analyzing 10,000 patient feedback forms to improve care quality.

**Goals**:
- Identify areas for improvement
- Track sentiment trends over time
- Categorize specific complaints and compliments
- Support quality improvement initiatives

### Step 1: Healthcare-Specific Considerations

#### Regulatory Compliance
- **HIPAA Compliance**: Remove all personal health information
- **Data Security**: Secure processing environment
- **Audit Trail**: Document all processing steps
- **Patient Privacy**: Anonymization protocols

#### Domain-Specific Labels
```csv
label
clinical_care_quality
nurse_communication
physician_communication
wait_times
facility_cleanliness
pain_management
discharge_process
billing_financial
staff_courtesy
medical_outcomes
```

### Step 2: Validation with Healthcare Experts

#### Expert Panel
- **Chief Medical Officer**: Clinical perspective
- **Patient Experience Director**: Operational insight
- **Quality Improvement Manager**: Process expertise
- **Data Analyst**: Technical validation

#### Validation Protocol
1. **Sample Selection**: 200 representative feedback forms
2. **Independent Coding**: Each expert codes separately
3. **Consensus Building**: Resolve disagreements through discussion
4. **AI Comparison**: Test AI performance against expert consensus

### Step 3: Phased Processing

#### Phase 1: Pilot (1,000 forms)
- **Processing Method**: Live multi-label classification
- **Model**: gpt-4o (balance accuracy and cost)
- **Validation**: 100-form manual check
- **Refinement**: Adjust labels based on results

#### Phase 2: Full Scale (remaining 9,000 forms)
- **Processing Method**: Batch processing
- **Quality Control**: 500-form validation sample
- **Timeline**: 48-hour processing window
- **Monitoring**: Real-time error tracking

### Step 4: Healthcare Quality Integration

#### Quality Metrics Integration
**Link to Hospital Metrics**:
- Patient satisfaction scores (HCAHPS)
- Clinical quality indicators
- Operational efficiency measures
- Staff performance data

#### Actionable Insights
**Example Findings**:
1. **Wait Times**: 34% of negative feedback mentions delays
2. **Communication**: 28% cite poor nurse communication
3. **Pain Management**: 15% report inadequate pain control
4. **Facility**: 12% mention cleanliness concerns

#### Quality Improvement Actions
1. **Staffing Analysis**: Correlate wait time complaints with staffing levels
2. **Communication Training**: Target specific communication issues
3. **Process Improvement**: Address systematic bottlenecks
4. **Facility Management**: Prioritize cleanliness in problem areas

---

## 📈 Workflow Comparison Matrix

| Workflow | Dataset Size | Processing Method | Model Used | Cost | Timeline | Accuracy |
|----------|-------------|------------------|------------|------|----------|----------|
| Customer Reviews | 5,000 | Batch | gpt-4o-mini | $0.30 | 5 days | 89% |
| Academic Research | 800 | Mixed | gpt-4o | $2.50 | 5 days | 86% |
| Content Moderation | 50,000 | Batch | gpt-4-turbo | $75 | 2 days | 94% |
| Healthcare Feedback | 10,000 | Batch | gpt-4o | $15 | 3 days | 91% |

## 🎯 Key Success Factors

### Across All Workflows
1. **Clear Objectives**: Well-defined goals and success criteria
2. **Label Quality**: Careful design and testing of classification schemes
3. **Validation Strategy**: Systematic comparison with human experts
4. **Iterative Refinement**: Continuous improvement based on results
5. **Documentation**: Thorough recording of decisions and methods

### Workflow-Specific Insights
- **Commercial Applications**: Focus on cost-efficiency and scalability
- **Academic Research**: Emphasis on methodological rigor and validation
- **Content Moderation**: Prioritize accuracy and bias detection
- **Healthcare**: Strict compliance and expert validation requirements

## 🔄 Adaptation Guidelines

### Customizing These Workflows

#### 1. Scale Adjustment
- **Smaller Projects**: Use live processing, reduce validation sample sizes
- **Larger Projects**: Increase batch sizes, implement more quality controls
- **Resource Constraints**: Use cheaper models, simpler label sets

#### 2. Domain Adaptation
- **Legal Documents**: Use precise legal terminology
- **Technical Content**: Adapt for specialized vocabulary
- **International**: Consider cultural and linguistic differences
- **Historical Data**: Account for language evolution over time

#### 3. Quality Requirements
- **Exploratory Analysis**: Lower accuracy acceptable for initial insights
- **Publication Research**: High accuracy and validation standards
- **Operational Decisions**: Balance accuracy with processing speed
- **Regulatory Compliance**: Maximum accuracy and documentation

---

*Ready to start your own project? Use these workflows as templates and adapt them to your specific needs. Remember to start small, validate carefully, and scale gradually for best results.*