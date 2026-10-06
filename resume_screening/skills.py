"""Skill taxonomy and a rule-based skill extractor.

Each line of ``_TAXONOMY`` is ``category | Canonical name | aliases | cs-aliases``:

* ``aliases`` are matched case-insensitively.
* ``cs-aliases`` are ambiguous English words (``Excel``, ``React``, ``Spring``)
  matched case-sensitively and only when they do not look like an ordinary
  verb/noun in a sentence.
"""
from __future__ import annotations

import re
from functools import lru_cache

_TAXONOMY = """
language|Python|python; python3; python 3
language|Java|java; core java; java ee; j2ee; java 8; java 11; java 17
language|JavaScript|javascript; ecmascript; es6; es2015|JS
language|TypeScript|typescript
language|C++|c++; cpp
language|C#|c#; csharp; c sharp
language|C|c programming; c language
language|Go|golang; go lang|
language|Rust||Rust
language|Ruby|ruby
language|PHP|php
language|Swift|swiftui; swift programming; swift 5|Swift
language|Kotlin|kotlin
language|Scala|scala
language|R|r programming; r language; rstudio|R
language|SQL|sql; t-sql; tsql; pl/sql; plsql; structured query language
language|MATLAB|matlab
language|Shell Scripting|bash; shell scripting; shell script; shell scripts; powershell; zsh
language|HTML|html; html5
language|CSS|css; css3; sass; scss
language|Dart|dart
ml|Machine Learning|machine learning; supervised learning; unsupervised learning; predictive modeling; predictive modelling; predictive models|ML
ml|Deep Learning|deep learning; neural networks; neural network; cnn; rnn; lstm; convolutional neural networks
ml|NLP|nlp; natural language processing; text mining; text classification; sentiment analysis; named entity recognition; spacy; nltk
ml|Computer Vision|computer vision; opencv; image processing; object detection; image classification
ml|Scikit-learn|scikit-learn; sklearn; scikit learn
ml|TensorFlow|tensorflow; tf serving
ml|Keras|keras
ml|PyTorch|pytorch
ml|Gradient Boosting|xgboost; lightgbm; catboost; gradient boosting; random forest; random forests
ml|LLMs|llm; llms; large language model; large language models; generative ai; genai; langchain; prompt engineering; retrieval augmented generation; hugging face; huggingface
ml|Statistics|statistics; statistical analysis; statistical modeling; statistical modelling; hypothesis testing; a/b testing; ab testing; regression analysis; probability
ml|Feature Engineering|feature engineering; feature selection; hyperparameter tuning; model evaluation; cross-validation
ml|MLOps|mlops; mlflow; kubeflow; model deployment; model serving; model monitoring; sagemaker
ml|Time Series|time series; time-series; forecasting; arima; prophet
ml|Recommender Systems|recommender systems; recommendation systems; recommendation engine; recommender system
ml|Pandas|pandas
ml|NumPy|numpy
ml|SciPy|scipy
ml|Jupyter|jupyter; jupyter notebook; jupyter notebooks; colab
data|Excel|ms excel; microsoft excel; advanced excel; excel vba; vba; pivot tables; pivot table; vlookup|Excel
data|Tableau|tableau
data|Power BI|power bi; powerbi; dax
data|Looker|looker; looker studio; qlik; qlikview; metabase
data|Data Visualization|data visualization; data visualisation; matplotlib; seaborn; plotly; dashboards; dashboarding; data storytelling
data|Data Analysis|data analysis; data analytics; exploratory data analysis; eda; data mining; data cleaning; data wrangling; data cleansing
data|Business Intelligence|business intelligence; bi reporting; kpi reporting; reporting
data|ETL|etl; elt; data pipelines; data pipeline; etl pipelines; etl pipeline; data ingestion
data|Apache Spark|pyspark; apache spark; spark sql; spark streaming|Spark
data|Hadoop|hadoop; hdfs; mapreduce; hive; apache hive; hbase
data|Kafka|kafka; apache kafka; kafka streams; kinesis
data|Airflow|airflow; apache airflow; dagster; prefect; luigi
data|dbt|dbt
data|Snowflake|snowflake
data|BigQuery|bigquery; big query
data|Redshift|redshift; amazon redshift
data|Databricks|databricks; delta lake
data|Data Warehousing|data warehouse; data warehousing; data warehouses; data modeling; data modelling; dimensional modeling; star schema
data|MySQL|mysql; mariadb
data|PostgreSQL|postgresql; postgres; psql
data|SQL Server|sql server; mssql; ms sql; microsoft sql server; ssis; ssrs
data|Oracle|oracle; oracle db; oracle database
data|MongoDB|mongodb; mongo
data|Redis|redis; memcached
data|Elasticsearch|elasticsearch; elastic search; elk stack; opensearch; kibana; logstash
data|SQLite|sqlite
data|Cassandra|cassandra
data|DynamoDB|dynamodb
data|NoSQL|nosql
web|React|reactjs; react.js; react js; react hooks|React
web|Angular|angular; angularjs; angular 2; rxjs; ngrx
web|Vue.js|vue; vue.js; vuejs; vue js; vuex; nuxt; nuxt.js; pinia
web|Next.js|next.js; nextjs
web|Node.js|node.js; nodejs; node js|Node
web|Express|express.js; expressjs|Express
web|Redux|redux; redux toolkit; zustand; mobx
web|jQuery|jquery
web|Tailwind CSS|tailwind; tailwindcss; tailwind css
web|Bootstrap|bootstrap; material ui; material-ui; chakra ui; ant design
web|Webpack|webpack; vite; babel; rollup; npm; yarn
web|Responsive Design|responsive design; responsive web design; mobile-first; cross-browser; cross browser; media queries
web|REST APIs|rest; restful; rest api; rest apis; restful api; restful apis; restful services; api development; api design; web services
web|GraphQL|graphql; apollo
web|Django|django; django rest framework; drf
web|Flask|flask
web|FastAPI|fastapi
web|Spring Boot|spring boot; springboot; spring framework; spring mvc; spring cloud|Spring
web|Hibernate|hibernate; jpa; mybatis
web|.NET|.net; dotnet; asp.net; .net core; entity framework; blazor
web|Ruby on Rails|ruby on rails; rails|RoR
web|Laravel|laravel; symfony; codeigniter
web|Microservices|microservices; microservice; micro-services; service-oriented architecture
web|Web Accessibility|accessibility; wcag; a11y; aria
web|Figma|figma; adobe xd; sketch; wireframes; wireframing; prototyping
web|Jest|jest; mocha; jasmine; enzyme; react testing library; karma
web|Authentication|jwt; oauth; oauth2; authentication; authorization; saml; openid
web|Message Queues|rabbitmq; sqs; activemq; message queue; message queues; celery; pub/sub
mobile|Android|android; android sdk; android studio; jetpack compose; android development; room database
mobile|iOS|ios; xcode; cocoa touch; uikit; ios development; core data
mobile|Flutter|flutter
mobile|React Native|react native; react-native; expo
mobile|Firebase|firebase; firestore; fcm
mobile|Mobile Development|mobile app development; mobile development; mobile applications; mobile app; mobile apps; play store; app store
devops|AWS|aws; amazon web services; ec2; cloudformation; amazon s3; aws lambda; ecs; cloudwatch; iam roles
devops|Azure|azure; microsoft azure; azure devops
devops|GCP|gcp; google cloud; google cloud platform; gke
devops|Docker|docker; docker compose; dockerfile; containerization; containerisation; containers
devops|Kubernetes|kubernetes; k8s; helm; eks; aks; openshift
devops|Terraform|terraform; infrastructure as code; iac; pulumi
devops|Configuration Management|ansible; chef; puppet; saltstack; configuration management
devops|CI/CD|ci/cd; ci cd; cicd; continuous integration; continuous delivery; continuous deployment; build pipelines; deployment pipelines
devops|Jenkins|jenkins
devops|GitHub Actions|github actions
devops|GitLab CI|gitlab ci; gitlab ci/cd; gitlab-ci; circleci; travis ci; argo cd; argocd; teamcity
devops|Git|git; github; gitlab; bitbucket; version control
devops|Linux|linux; unix; ubuntu; centos; red hat; rhel; debian
devops|Monitoring|prometheus; grafana; datadog; nagios; new relic; monitoring and alerting; observability; splunk; opentelemetry
devops|Nginx|nginx; apache http server; load balancing; load balancer; haproxy
devops|Networking|networking; tcp/ip; dns; vpn; dhcp; routing and switching; subnetting; cisco
devops|SRE|sre; site reliability engineering; site reliability; incident management; on-call; slo; slos
test|Selenium|selenium; selenium webdriver; webdriverio
test|Cypress|cypress
test|Playwright|playwright; puppeteer; testcafe
test|JUnit|junit; testng; mockito; nunit; xunit
test|PyTest|pytest; unittest; robot framework
test|Postman|postman; soapui; api testing; swagger; openapi
test|Performance Testing|jmeter; load testing; performance testing; gatling; locust; stress testing; loadrunner
test|Manual Testing|manual testing; test cases; test case design; exploratory testing; regression testing; smoke testing; sanity testing; functional testing; uat; user acceptance testing; test plans; test plan
test|Test Automation|test automation; automation testing; automated testing; test automation framework; automation framework
test|Jira|jira; bug tracking; defect tracking; bugzilla; testrail; zephyr
test|BDD|bdd; cucumber; gherkin; behave; behavior driven development
test|TDD|tdd; test driven development; test-driven development
test|Appium|appium; browserstack; espresso; xcuitest
test|Unit Testing|unit testing; unit tests; integration testing; integration tests; code coverage
security|Cybersecurity|cybersecurity; cyber security; information security; infosec; security operations; security controls
security|Penetration Testing|penetration testing; pentesting; pen testing; ethical hacking; vulnerability assessment; vulnerability scanning; vapt; red team; red teaming
security|SIEM|siem; qradar; sentinel; log analysis; security monitoring; edr; crowdstrike; soc analyst
security|Wireshark|wireshark; packet analysis; tcpdump; packet capture
security|Nmap|nmap; nessus; openvas; qualys; nikto
security|Metasploit|metasploit; burp suite; kali linux; sqlmap; john the ripper; hydra
security|Network Security|network security; firewall; firewalls; ids/ips; intrusion detection; intrusion prevention; palo alto; fortinet; waf
security|Incident Response|incident response; threat hunting; threat detection; digital forensics; malware analysis; threat intelligence; mitre att&ck; soc; forensics
security|Compliance|iso 27001; nist; pci dss; pci-dss; gdpr; hipaa; soc 2; risk assessment; compliance; security audits; security audit; grc
security|Cryptography|cryptography; encryption; pki; ssl/tls; tls; ssl; vpn security
security|OWASP|owasp; owasp top 10; application security; appsec; secure coding; sast; dast; devsecops
security|IAM|iam; identity and access management; active directory; sso; mfa; privileged access management; ldap
business|Requirements Gathering|requirements gathering; requirement gathering; requirements analysis; requirement analysis; business requirements; brd; frd; user stories; requirements elicitation; functional requirements; requirement documentation
business|Stakeholder Management|stakeholder management; stakeholder communication; stakeholder engagement
business|Process Modeling|process mapping; process improvement; process modeling; bpmn; uml; use cases; use case; workflow analysis; business process; business processes; visio
business|Agile|agile; scrum; kanban; sprint planning; safe; scrum master; product backlog; backlog grooming
business|Project Management|project management; pmp; prince2; project planning; project coordination; ms project; trello; asana
business|Gap Analysis|gap analysis; swot; cost benefit analysis; cost-benefit analysis; feasibility study; root cause analysis; impact analysis; market research
business|Documentation|documentation; technical documentation; confluence; technical writing
business|Product Analytics|product analytics; google analytics; mixpanel; amplitude; funnel analysis; cohort analysis; kpis; kpi; metrics
cs|Data Structures & Algorithms|data structures; algorithms; dsa; data structures and algorithms; competitive programming; leetcode
cs|OOP|oop; oops; object oriented programming; object-oriented programming; object oriented design; design patterns; solid principles
cs|System Design|system design; distributed systems; scalability; high availability; low latency; scalable systems; high-performance
cs|Performance Optimization|performance optimization; performance optimisation; performance tuning; code optimization; query optimization; profiling
cs|Database Design|database design; schema design; database management; rdbms; relational databases; stored procedures; indexing; normalization
cs|Caching|caching; cdn; cloudflare
soft|Communication|communication skills; communication; presentation skills; presentations; written communication; verbal communication
soft|Leadership|leadership; team lead; team leadership; mentoring; mentored; mentorship; led a team; leading a team
soft|Problem Solving|problem solving; problem-solving; analytical skills; critical thinking; analytical thinking; troubleshooting
soft|Teamwork|teamwork; collaboration; cross-functional; team player; collaborative
"""

# Skills of the same family give partial credit when the JD asks for one and
# the resume lists another (e.g. JD wants PostgreSQL, resume has MySQL).
_RELATED_GROUPS = [
    {"MySQL", "PostgreSQL", "SQL Server", "Oracle", "SQLite", "SQL", "Database Design"},
    {"AWS", "Azure", "GCP"},
    {"TensorFlow", "PyTorch", "Keras", "Deep Learning"},
    {"React", "Angular", "Vue.js", "Next.js"},
    {"Tableau", "Power BI", "Looker", "Data Visualization"},
    {"Jenkins", "GitHub Actions", "GitLab CI", "CI/CD"},
    {"JUnit", "PyTest", "Unit Testing", "Jest"},
    {"Selenium", "Cypress", "Playwright", "Test Automation", "Appium"},
    {"Kafka", "Message Queues"},
    {"Django", "Flask", "FastAPI"},
    {"Spring Boot", "Hibernate", "Java"},
    {"Docker", "Kubernetes"},
    {"Terraform", "Configuration Management"},
    {"Redshift", "BigQuery", "Snowflake", "Data Warehousing", "Databricks"},
    {"Apache Spark", "Hadoop", "Databricks"},
    {"MongoDB", "NoSQL", "Cassandra", "DynamoDB", "Redis"},
    {"Machine Learning", "Scikit-learn", "Gradient Boosting", "Feature Engineering", "Statistics"},
    {"NLP", "LLMs"},
    {"Android", "iOS", "Flutter", "React Native", "Mobile Development"},
    {"SIEM", "Incident Response", "Monitoring"},
    {"Penetration Testing", "Metasploit", "Nmap", "OWASP"},
    {"Agile", "Project Management"},
    {"Data Analysis", "Business Intelligence", "Excel", "Product Analytics"},
    {"REST APIs", "Microservices", "GraphQL"},
    {"Python", "Pandas", "NumPy"},
]

_AMBIGUOUS_GUARD = r"(?!\s+(?:in|at|to|as|on|the|your|their|our|with|for)\b)(?!\s+\d)"


class Skill:
    __slots__ = ("name", "category", "aliases", "cs_aliases", "slug")

    def __init__(self, name, category, aliases, cs_aliases):
        self.name = name
        self.category = category
        self.aliases = aliases
        self.cs_aliases = cs_aliases
        self.slug = slugify(name)


def slugify(name: str) -> str:
    """Token used in the ML vocabulary for a canonical skill (c++ -> cpp)."""
    s = name.lower().replace("c++", "cpp").replace("c#", "csharp").replace(".net", "dotnet")
    s = s.replace("&", "and").replace(".", "")
    return "skill_" + re.sub(r"[^a-z0-9]+", "_", s).strip("_")


def _parse_taxonomy() -> list[Skill]:
    skills = []
    for line in _TAXONOMY.strip().splitlines():
        parts = line.split("|")
        category, name = parts[0].strip(), parts[1].strip()
        aliases = [a.strip().lower() for a in (parts[2] if len(parts) > 2 else "").split(";") if a.strip()]
        cs_aliases = [a.strip() for a in (parts[3] if len(parts) > 3 else "").split(";") if a.strip()]
        # the canonical name itself is always an alias (unless declared ambiguous)
        if name.lower() not in aliases and name not in cs_aliases:
            aliases.append(name.lower())
        skills.append(Skill(name, category, aliases, cs_aliases))
    return skills


SKILLS: list[Skill] = _parse_taxonomy()
SKILL_BY_NAME: dict[str, Skill] = {s.name: s for s in SKILLS}


def _alias_pattern(alias: str) -> str:
    esc = re.escape(alias).replace(r"\ ", r"[\s\-]+")
    return esc


@lru_cache(maxsize=1)
def _compiled():
    ci_map: dict[str, str] = {}
    cs_map: dict[str, str] = {}
    for s in SKILLS:
        for a in s.aliases:
            ci_map.setdefault(a, s.name)
        for a in s.cs_aliases:
            cs_map.setdefault(a, s.name)

    def build(mapping, flags, guard=""):
        keys = sorted(mapping, key=len, reverse=True)
        body = "|".join(_alias_pattern(k) for k in keys)
        pattern = rf"(?<![\w+#.])(?:{body})(?![\w+#])(?!\.\w){guard}"
        return re.compile(pattern, flags)

    ci_re = build(ci_map, re.IGNORECASE)
    cs_re = build(cs_map, 0, _AMBIGUOUS_GUARD)
    return ci_re, cs_re, ci_map, cs_map


def _lookup(match_text: str, ci_map: dict, cs_map: dict) -> str | None:
    norm = re.sub(r"[\s\-]+", " ", match_text.lower())
    return ci_map.get(norm)


def find_skill_spans(text: str) -> list[tuple[int, int, str]]:
    """Return non-overlapping ``(start, end, canonical)`` skill mentions."""
    ci_re, cs_re, ci_map, cs_map = _compiled()
    spans: list[tuple[int, int, str]] = []
    for m in ci_re.finditer(text):
        name = _lookup(m.group(0), ci_map, cs_map)
        if name:
            spans.append((m.start(), m.end(), name))
    for m in cs_re.finditer(text):
        name = cs_map.get(re.sub(r"[\s\-]+", " ", m.group(0)))
        if name:
            spans.append((m.start(), m.end(), name))
    spans.sort(key=lambda s: (s[0], -(s[1] - s[0])))
    out, last_end = [], -1
    for s in spans:
        if s[0] >= last_end:
            out.append(s)
            last_end = s[1]
    return out


def extract_skills(text: str) -> list[str]:
    """Unique canonical skills mentioned in ``text`` (first-mention order)."""
    seen: dict[str, None] = {}
    for _, _, name in find_skill_spans(text):
        seen.setdefault(name)
    return list(seen)


def skill_category(name: str) -> str:
    s = SKILL_BY_NAME.get(name)
    return s.category if s else "other"


@lru_cache(maxsize=1)
def _related_index() -> dict[str, set[str]]:
    idx: dict[str, set[str]] = {}
    for group in _RELATED_GROUPS:
        for s in group:
            idx.setdefault(s, set()).update(group - {s})
    return idx


def related_skills(name: str) -> set[str]:
    return _related_index().get(name, set())
