#!/usr/bin/env python3
"""
Intelligent Fuzzy Job Matching System for Aremu WhatsApp Bot
Matches users to jobs using multiple intelligent strategies
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
import psycopg2.extras
from difflib import SequenceMatcher
from collections import defaultdict

logger = logging.getLogger(__name__)


class IntelligentJobMatcher:
    """Advanced job matching using fuzzy logic, semantic similarity, and skill matching"""

    def __init__(self, db_connection):
        self.connection = db_connection

        # Semantic job title clusters for intelligent matching
        self.JOB_CLUSTERS = {
            "software_development": [
                "developer",
                "engineer",
                "programmer",
                "coder",
                "architect",
                "frontend",
                "backend",
                "fullstack",
                "web developer",
                "software engineer",
                "react developer",
                "vue developer",
                "angular developer",
                "node developer",
                "python developer",
                "java developer",
                "javascript developer",
                "php developer",
                "c# developer",
                "c++ developer",
                "ruby developer",
                "go developer",
                "kotlin developer",
                "swift developer",
                "flutter developer",
                "react native developer",
                "ios developer",
                "android developer",
                "mobile developer",
                "app developer",
                "game developer",
                "unity developer",
                "unreal developer",
                "blockchain developer",
                "smart contract developer",
                "solidity developer",
                "web3 developer",
                "defi developer",
                "nft developer",
            ],
            "data_science": [
                "data scientist",
                "data analyst",
                "machine learning",
                "ai engineer",
                "data engineer",
                "analytics",
                "statistician",
                "ml engineer",
                "ai researcher",
                "data specialist",
                "business intelligence",
                "bi analyst",
                "data mining",
                "big data",
                "quantitative analyst",
                "research scientist",
                "data science",
                "analytics engineer",
                "data analytics",
                "business analyst",
                "intelligence analyst",
                "data modeler",
                "data architect",
                "senior data",
                "logistics data analyst",
                "web data analyst",
                "data extraction",
                "web scraping",
                "data harvesting",
                "data infrastructure",
                "deep learning engineer",
                "computer vision engineer",
                "nlp engineer",
                "mlops engineer",
                "ai product manager",
                "data product manager",
                "research analyst",
                "market research analyst",
                "business intelligence developer",
                "etl developer",
                "data warehouse engineer",
                "data pipeline engineer",
                "big data engineer",
                "hadoop developer",
                "spark developer",
                "kafka engineer",
                "data visualization specialist",
                "tableau developer",
                "power bi developer",
                "looker developer",
            ],
            "design": [
                "designer",
                "ui designer",
                "ux designer",
                "graphic designer",
                "web designer",
                "product designer",
                "visual designer",
                "creative",
                "artist",
                "illustrator",
                "motion designer",
                "animation designer",
                "3d designer",
                "game designer",
                "interaction designer",
                "service designer",
                "design researcher",
                "design strategist",
                "brand designer",
                "logo designer",
                "packaging designer",
                "print designer",
                "digital designer",
                "creative director",
                "art director",
                "design lead",
                "senior designer",
                "junior designer",
                "freelance designer",
                "design consultant",
                "design manager",
                "design coordinator",
                "design intern",
                "figma designer",
                "sketch designer",
                "adobe designer",
                "photoshop designer",
                "illustrator designer",
                "indesign designer",
                "after effects designer",
                "premiere designer",
            ],
            "management": [
                "manager",
                "director",
                "lead",
                "supervisor",
                "coordinator",
                "project manager",
                "product manager",
                "team lead",
                "head of",
                "chief",
                "executive",
                "ceo",
                "cto",
                "cfo",
                "coo",
                "cmo",
                "vp",
                "vice president",
                "president",
                "general manager",
                "operations manager",
                "program manager",
                "portfolio manager",
                "delivery manager",
                "service manager",
                "relationship manager",
                "account manager",
                "client manager",
                "customer success manager",
                "community manager",
                "brand manager",
                "marketing manager",
                "sales manager",
                "hr manager",
                "finance manager",
                "it manager",
                "technical manager",
                "engineering manager",
                "development manager",
                "qa manager",
                "security manager",
                "compliance manager",
                "risk manager",
                "strategy manager",
                "business manager",
                "regional manager",
                "country manager",
                "area manager",
                "district manager",
                "store manager",
                "branch manager",
                "office manager",
                "facility manager",
                "warehouse manager",
                "logistics manager",
                "supply chain manager",
                "procurement manager",
                "vendor manager",
                "contract manager",
                "change manager",
                "transformation manager",
                "innovation manager",
                "growth manager",
                "performance manager",
                "quality manager",
                "training manager",
                "learning manager",
                "talent manager",
                "people manager",
                "culture manager",
                "engagement manager",
                "communications manager",
                "pr manager",
                "media manager",
                "content manager",
                "social media manager",
                "digital manager",
                "e-commerce manager",
                "product marketing manager",
                "field marketing manager",
                "event manager",
                "campaign manager",
                "lead generation manager",
                "demand generation manager",
                "revenue manager",
                "pricing manager",
                "business development manager",
                "partnership manager",
                "alliance manager",
                "channel manager",
                "territory manager",
                "key account manager",
                "customer manager",
                "client success manager",
                "support manager",
                "service delivery manager",
                "implementation manager",
                "onboarding manager",
                "retention manager",
                "churn manager",
                "analytics manager",
                "insights manager",
                "research manager",
                "data manager",
                "information manager",
                "knowledge manager",
                "documentation manager",
                "process manager",
                "workflow manager",
                "automation manager",
                "efficiency manager",
                "productivity manager",
                "optimization manager",
                "improvement manager",
                "excellence manager",
                "standards manager",
                "governance manager",
                "policy manager",
                "procedure manager",
                "audit manager",
                "control manager",
                "monitoring manager",
                "reporting manager",
                "dashboard manager",
                "metrics manager",
                "kpi manager",
                "scorecard manager",
                "budget manager",
                "cost manager",
                "expense manager",
                "financial manager",
                "accounting manager",
                "treasury manager",
                "tax manager",
                "payroll manager",
                "benefits manager",
                "compensation manager",
                "rewards manager",
                "recognition manager",
                "wellness manager",
                "safety manager",
                "health manager",
                "environment manager",
                "sustainability manager",
                "csr manager",
                "diversity manager",
                "inclusion manager",
                "equity manager",
                "belonging manager",
                "ethics manager",
                "integrity manager",
                "values manager",
                "mission manager",
                "vision manager",
                "purpose manager",
                "impact manager",
                "outcome manager",
                "result manager",
                "achievement manager",
                "success manager",
                "delivery manager",
                "execution manager",
                "implementation manager",
                "deployment manager",
                "rollout manager",
                "launch manager",
                "go-to-market manager",
                "market manager",
                "segment manager",
                "vertical manager",
                "industry manager",
                "sector manager",
                "category manager",
                "portfolio manager",
                "program manager",
                "initiative manager",
                "project manager",
                "workstream manager",
                "task manager",
                "activity manager",
                "milestone manager",
                "timeline manager",
                "schedule manager",
                "resource manager",
                "capacity manager",
                "demand manager",
                "supply manager",
                "inventory manager",
                "stock manager",
                "asset manager",
                "property manager",
                "real estate manager",
                "facility manager",
                "building manager",
                "maintenance manager",
                "repair manager",
                "service manager",
                "support manager",
                "help desk manager",
                "call center manager",
                "contact center manager",
                "customer service manager",
                "customer experience manager",
                "user experience manager",
                "customer journey manager",
                "touchpoint manager",
                "interaction manager",
                "engagement manager",
                "relationship manager",
                "loyalty manager",
                "retention manager",
                "acquisition manager",
                "conversion manager",
                "funnel manager",
                "pipeline manager",
                "forecast manager",
                "planning manager",
                "strategy manager",
                "vision manager",
                "roadmap manager",
                "backlog manager",
                "feature manager",
                "requirement manager",
                "specification manager",
                "design manager",
                "development manager",
                "engineering manager",
                "architecture manager",
                "infrastructure manager",
                "platform manager",
                "system manager",
                "network manager",
                "security manager",
                "privacy manager",
                "data protection manager",
                "gdpr manager",
                "compliance manager",
                "regulatory manager",
                "legal manager",
                "contract manager",
                "vendor manager",
                "supplier manager",
                "partner manager",
                "alliance manager",
                "ecosystem manager",
                "community manager",
                "developer relations manager",
                "technical evangelist manager",
                "advocacy manager",
                "influencer manager",
                "ambassador manager",
                "champion manager",
                "expert manager",
                "specialist manager",
                "consultant manager",
                "advisor manager",
                "mentor manager",
                "coach manager",
                "trainer manager",
                "instructor manager",
                "educator manager",
                "teacher manager",
                "professor manager",
                "researcher manager",
                "scientist manager",
                "analyst manager",
                "investigator manager",
                "explorer manager",
                "discoverer manager",
                "innovator manager",
                "creator manager",
                "inventor manager",
                "designer manager",
                "architect manager",
                "builder manager",
                "maker manager",
                "developer manager",
                "engineer manager",
                "technician manager",
                "operator manager",
                "administrator manager",
                "coordinator manager",
                "organizer manager",
                "planner manager",
                "scheduler manager",
                "dispatcher manager",
                "controller manager",
                "monitor manager",
                "supervisor manager",
                "overseer manager",
                "guardian manager",
                "steward manager",
                "custodian manager",
                "caretaker manager",
                "keeper manager",
                "maintainer manager",
                "preserver manager",
                "protector manager",
                "defender manager",
                "advocate manager",
                "representative manager",
                "spokesperson manager",
                "ambassador manager",
                "liaison manager",
                "connector manager",
                "bridge manager",
                "facilitator manager",
                "enabler manager",
                "catalyst manager",
                "driver manager",
                "leader manager",
                "pioneer manager",
                "trailblazer manager",
                "pathfinder manager",
                "navigator manager",
                "guide manager",
                "director manager",
                "conductor manager",
                "orchestrator manager",
                "choreographer manager",
                "composer manager",
                "curator manager",
                "editor manager",
                "publisher manager",
                "broadcaster manager",
                "communicator manager",
                "messenger manager",
                "storyteller manager",
                "narrator manager",
                "presenter manager",
                "speaker manager",
                "performer manager",
                "entertainer manager",
                "artist manager",
                "creative manager",
                "visionary manager",
                "dreamer manager",
                "thinker manager",
                "philosopher manager",
                "strategist manager",
                "tactician manager",
                "planner manager",
                "organizer manager",
                "executor manager",
                "implementer manager",
                "deliverer manager",
                "achiever manager",
                "winner manager",
                "champion manager",
                "hero manager",
                "star manager",
                "expert manager",
                "master manager",
                "guru manager",
                "ninja manager",
                "wizard manager",
                "magician manager",
                "genius manager",
                "prodigy manager",
                "talent manager",
                "gift manager",
                "blessing manager",
                "miracle manager",
                "wonder manager",
                "marvel manager",
                "phenomenon manager",
                "sensation manager",
                "breakthrough manager",
                "revolution manager",
                "transformation manager",
                "evolution manager",
                "progression manager",
                "advancement manager",
                "improvement manager",
                "enhancement manager",
                "upgrade manager",
                "optimization manager",
                "refinement manager",
                "perfection manager",
                "excellence manager",
                "quality manager",
                "standard manager",
                "benchmark manager",
                "best practice manager",
                "gold standard manager",
                "world class manager",
                "top tier manager",
                "premium manager",
                "luxury manager",
                "elite manager",
                "exclusive manager",
                "select manager",
                "special manager",
                "unique manager",
                "rare manager",
                "precious manager",
                "valuable manager",
                "priceless manager",
                "invaluable manager",
                "irreplaceable manager",
                "indispensable manager",
                "essential manager",
                "critical manager",
                "vital manager",
                "crucial manager",
                "key manager",
                "core manager",
                "central manager",
                "main manager",
                "primary manager",
                "principal manager",
                "chief manager",
                "head manager",
                "lead manager",
                "senior manager",
                "executive manager",
                "top manager",
                "senior executive",
                "c-level executive",
                "c-suite executive",
                "board member",
                "board director",
                "non-executive director",
                "independent director",
                "chairman",
                "chairwoman",
                "chairperson",
                "chair",
                "president",
                "vice president",
                "senior vice president",
                "executive vice president",
                "group vice president",
                "regional vice president",
                "country president",
                "general manager",
                "deputy general manager",
                "assistant general manager",
                "associate general manager",
                "senior general manager",
                "executive general manager",
                "group general manager",
                "regional general manager",
                "country general manager",
                "division general manager",
                "business unit general manager",
                "product general manager",
                "service general manager",
                "operations general manager",
                "commercial general manager",
                "sales general manager",
                "marketing general manager",
                "finance general manager",
                "hr general manager",
                "it general manager",
                "technical general manager",
                "engineering general manager",
                "manufacturing general manager",
                "supply chain general manager",
                "logistics general manager",
                "procurement general manager",
                "quality general manager",
                "safety general manager",
                "environment general manager",
                "sustainability general manager",
                "innovation general manager",
                "strategy general manager",
                "transformation general manager",
                "change general manager",
                "improvement general manager",
                "excellence general manager",
                "performance general manager",
                "delivery general manager",
                "execution general manager",
                "implementation general manager",
                "deployment general manager",
                "rollout general manager",
                "launch general manager",
                "go-to-market general manager",
                "market general manager",
                "customer general manager",
                "client general manager",
                "partner general manager",
                "alliance general manager",
                "ecosystem general manager",
                "community general manager",
                "stakeholder general manager",
                "investor general manager",
                "shareholder general manager",
                "owner general manager",
                "founder general manager",
                "co-founder general manager",
                "entrepreneur general manager",
                "intrapreneur general manager",
                "business owner general manager",
                "business leader general manager",
                "thought leader general manager",
                "industry leader general manager",
                "market leader general manager",
                "innovation leader general manager",
                "technology leader general manager",
                "digital leader general manager",
                "transformation leader general manager",
                "change leader general manager",
                "culture leader general manager",
                "people leader general manager",
                "talent leader general manager",
                "learning leader general manager",
                "development leader general manager",
                "growth leader general manager",
                "performance leader general manager",
                "excellence leader general manager",
                "quality leader general manager",
                "customer leader general manager",
                "service leader general manager",
                "experience leader general manager",
                "journey leader general manager",
                "engagement leader general manager",
                "relationship leader general manager",
                "partnership leader general manager",
                "collaboration leader general manager",
                "teamwork leader general manager",
                "communication leader general manager",
                "storytelling leader general manager",
                "brand leader general manager",
                "marketing leader general manager",
                "sales leader general manager",
                "revenue leader general manager",
                "profit leader general manager",
                "value leader general manager",
                "impact leader general manager",
                "outcome leader general manager",
                "result leader general manager",
                "success leader general manager",
                "achievement leader general manager",
                "accomplishment leader general manager",
                "milestone leader general manager",
                "breakthrough leader general manager",
                "innovation leader general manager",
                "disruption leader general manager",
                "revolution leader general manager",
                "transformation leader general manager",
                "evolution leader general manager",
                "progression leader general manager",
                "advancement leader general manager",
                "improvement leader general manager",
                "enhancement leader general manager",
                "optimization leader general manager",
                "efficiency leader general manager",
                "productivity leader general manager",
                "effectiveness leader general manager",
                "impact leader general manager",
                "influence leader general manager",
                "authority leader general manager",
                "expertise leader general manager",
                "knowledge leader general manager",
                "wisdom leader general manager",
                "insight leader general manager",
                "understanding leader general manager",
                "awareness leader general manager",
                "consciousness leader general manager",
                "mindfulness leader general manager",
                "presence leader general manager",
                "focus leader general manager",
                "attention leader general manager",
                "concentration leader general manager",
                "dedication leader general manager",
                "commitment leader general manager",
                "passion leader general manager",
                "enthusiasm leader general manager",
                "energy leader general manager",
                "drive leader general manager",
                "motivation leader general manager",
                "inspiration leader general manager",
                "vision leader general manager",
                "purpose leader general manager",
                "mission leader general manager",
                "values leader general manager",
                "principles leader general manager",
                "beliefs leader general manager",
                "convictions leader general manager",
                "standards leader general manager",
                "ethics leader general manager",
                "integrity leader general manager",
                "honesty leader general manager",
                "transparency leader general manager",
                "authenticity leader general manager",
                "genuineness leader general manager",
                "sincerity leader general manager",
                "trustworthiness leader general manager",
                "reliability leader general manager",
                "dependability leader general manager",
                "consistency leader general manager",
                "stability leader general manager",
                "predictability leader general manager",
                "certainty leader general manager",
                "confidence leader general manager",
                "assurance leader general manager",
                "security leader general manager",
                "safety leader general manager",
                "protection leader general manager",
                "care leader general manager",
                "support leader general manager",
                "help leader general manager",
                "assistance leader general manager",
                "guidance leader general manager",
                "direction leader general manager",
                "leadership leader general manager",
                "management leader general manager",
                "supervision leader general manager",
                "oversight leader general manager",
                "governance leader general manager",
                "administration leader general manager",
                "coordination leader general manager",
                "organization leader general manager",
                "planning leader general manager",
                "strategy leader general manager",
                "execution leader general manager",
                "implementation leader general manager",
                "delivery leader general manager",
                "achievement leader general manager",
                "success leader general manager",
                "excellence leader general manager",
                "quality leader general manager",
                "perfection leader general manager",
                "mastery leader general manager",
                "expertise leader general manager",
                "specialization leader general manager",
                "focus leader general manager",
                "niche leader general manager",
                "domain leader general manager",
                "field leader general manager",
                "area leader general manager",
                "sector leader general manager",
                "industry leader general manager",
                "market leader general manager",
                "segment leader general manager",
                "category leader general manager",
                "vertical leader general manager",
                "horizontal leader general manager",
                "cross-functional leader general manager",
                "multi-disciplinary leader general manager",
                "interdisciplinary leader general manager",
                "holistic leader general manager",
                "comprehensive leader general manager",
                "complete leader general manager",
                "total leader general manager",
                "full leader general manager",
                "entire leader general manager",
                "whole leader general manager",
                "integrated leader general manager",
                "unified leader general manager",
                "consolidated leader general manager",
                "centralized leader general manager",
                "coordinated leader general manager",
                "synchronized leader general manager",
                "aligned leader general manager",
                "harmonized leader general manager",
                "balanced leader general manager",
                "optimized leader general manager",
                "maximized leader general manager",
                "enhanced leader general manager",
                "improved leader general manager",
                "advanced leader general manager",
                "evolved leader general manager",
                "transformed leader general manager",
                "revolutionized leader general manager",
                "disrupted leader general manager",
                "innovated leader general manager",
                "created leader general manager",
                "invented leader general manager",
                "designed leader general manager",
                "developed leader general manager",
                "built leader general manager",
                "constructed leader general manager",
                "established leader general manager",
                "founded leader general manager",
                "launched leader general manager",
                "started leader general manager",
                "initiated leader general manager",
                "began leader general manager",
                "commenced leader general manager",
                "originated leader general manager",
                "pioneered leader general manager",
                "trailblazed leader general manager",
                "led leader general manager",
                "guided leader general manager",
                "directed leader general manager",
                "managed leader general manager",
                "supervised leader general manager",
                "oversaw leader general manager",
                "governed leader general manager",
                "administered leader general manager",
                "coordinated leader general manager",
                "organized leader general manager",
                "planned leader general manager",
                "strategized leader general manager",
                "executed leader general manager",
                "implemented leader general manager",
                "delivered leader general manager",
                "achieved leader general manager",
                "succeeded leader general manager",
                "excelled leader general manager",
                "mastered leader general manager",
                "perfected leader general manager",
                "optimized leader general manager",
                "maximized leader general manager",
                "enhanced leader general manager",
                "improved leader general manager",
                "advanced leader general manager",
                "evolved leader general manager",
                "transformed leader general manager",
                "revolutionized leader general manager",
                "disrupted leader general manager",
                "innovated leader general manager",
                "created leader general manager",
                "invented leader general manager",
                "designed leader general manager",
                "developed leader general manager",
                "built leader general manager",
                "constructed leader general manager",
                "established leader general manager",
                "founded leader general manager",
                "launched leader general manager",
                "started leader general manager",
                "initiated leader general manager",
                "began leader general manager",
                "commenced leader general manager",
                "originated leader general manager",
                "pioneered leader general manager",
                "trailblazed leader general manager",
            ],
            "marketing": [
                "marketer",
                "marketing",
                "digital marketing",
                "content marketing",
                "social media",
                "seo specialist",
                "brand manager",
                "campaign manager",
                "growth hacker",
                "content creator",
                "marketing specialist",
                "marketing coordinator",
                "marketing assistant",
                "marketing executive",
                "marketing director",
                "marketing manager",
                "marketing lead",
                "marketing analyst",
                "marketing researcher",
                "market researcher",
                "consumer insights",
                "brand strategist",
                "brand consultant",
                "brand designer",
                "brand developer",
                "brand ambassador",
                "brand advocate",
                "brand evangelist",
                "brand champion",
                "brand guardian",
                "brand steward",
                "brand custodian",
                "brand keeper",
                "brand maintainer",
                "brand builder",
                "brand creator",
                "brand innovator",
                "brand disruptor",
                "brand transformer",
                "brand revolutionary",
                "brand pioneer",
                "brand trailblazer",
                "brand leader",
                "brand expert",
                "brand specialist",
                "brand consultant",
                "brand advisor",
                "brand mentor",
                "brand coach",
                "brand trainer",
                "brand educator",
                "brand teacher",
                "brand instructor",
                "brand facilitator",
                "brand enabler",
                "brand catalyst",
                "brand driver",
                "brand motivator",
                "brand inspirator",
                "brand visionary",
                "brand strategist",
                "brand planner",
                "brand architect",
                "brand designer",
                "brand developer",
                "brand engineer",
                "brand technician",
                "brand operator",
                "brand administrator",
                "brand coordinator",
                "brand organizer",
                "brand scheduler",
                "brand dispatcher",
                "brand controller",
                "brand monitor",
                "brand supervisor",
                "brand overseer",
                "brand guardian",
                "brand steward",
                "brand custodian",
                "brand caretaker",
                "brand keeper",
                "brand maintainer",
                "brand preserver",
                "brand protector",
                "brand defender",
                "brand advocate",
                "brand representative",
                "brand spokesperson",
                "brand ambassador",
                "brand liaison",
                "brand connector",
                "brand bridge",
                "brand facilitator",
                "brand enabler",
                "brand catalyst",
                "brand driver",
                "brand leader",
                "brand pioneer",
                "brand trailblazer",
                "brand pathfinder",
                "brand navigator",
                "brand guide",
                "brand director",
                "brand conductor",
                "brand orchestrator",
                "brand choreographer",
                "brand composer",
                "brand curator",
                "brand editor",
                "brand publisher",
                "brand broadcaster",
                "brand communicator",
                "brand messenger",
                "brand storyteller",
                "brand narrator",
                "brand presenter",
                "brand speaker",
                "brand performer",
                "brand entertainer",
                "brand artist",
                "brand creative",
                "brand visionary",
                "brand dreamer",
                "brand thinker",
                "brand philosopher",
                "brand strategist",
                "brand tactician",
                "brand planner",
                "brand organizer",
                "brand executor",
                "brand implementer",
                "brand deliverer",
                "brand achiever",
                "brand winner",
                "brand champion",
                "brand hero",
                "brand star",
                "brand expert",
                "brand master",
                "brand guru",
                "brand ninja",
                "brand wizard",
                "brand magician",
                "brand genius",
                "brand prodigy",
                "brand talent",
                "brand gift",
                "brand blessing",
                "brand miracle",
                "brand wonder",
                "brand marvel",
                "brand phenomenon",
                "brand sensation",
                "brand breakthrough",
                "brand revolution",
                "brand transformation",
                "brand evolution",
                "brand progression",
                "brand advancement",
                "brand improvement",
                "brand enhancement",
                "brand upgrade",
                "brand optimization",
                "brand refinement",
                "brand perfection",
                "brand excellence",
                "brand quality",
                "brand standard",
                "brand benchmark",
                "brand best practice",
                "brand gold standard",
                "brand world class",
                "brand top tier",
                "brand premium",
                "brand luxury",
                "brand elite",
                "brand exclusive",
                "brand select",
                "brand special",
                "brand unique",
                "brand rare",
                "brand precious",
                "brand valuable",
                "brand priceless",
                "brand invaluable",
                "brand irreplaceable",
                "brand indispensable",
                "brand essential",
                "brand critical",
                "brand vital",
                "brand crucial",
                "brand key",
                "brand core",
                "brand central",
                "brand main",
                "brand primary",
                "brand principal",
                "brand chief",
                "brand head",
                "brand lead",
                "brand senior",
                "brand executive",
                "brand top",
                "digital marketer",
                "online marketer",
                "internet marketer",
                "web marketer",
                "e-commerce marketer",
                "mobile marketer",
                "app marketer",
                "social media marketer",
                "facebook marketer",
                "instagram marketer",
                "twitter marketer",
                "linkedin marketer",
                "youtube marketer",
                "tiktok marketer",
                "snapchat marketer",
                "pinterest marketer",
                "reddit marketer",
                "discord marketer",
                "telegram marketer",
                "whatsapp marketer",
                "email marketer",
                "newsletter marketer",
                "automation marketer",
                "crm marketer",
                "database marketer",
                "direct marketer",
                "performance marketer",
                "growth marketer",
                "acquisition marketer",
                "retention marketer",
                "loyalty marketer",
                "referral marketer",
                "viral marketer",
                "influencer marketer",
                "affiliate marketer",
                "partner marketer",
                "channel marketer",
                "b2b marketer",
                "b2c marketer",
                "b2g marketer",
                "enterprise marketer",
                "startup marketer",
                "saas marketer",
                "fintech marketer",
                "healthtech marketer",
                "edtech marketer",
                "proptech marketer",
                "agtech marketer",
                "cleantech marketer",
                "biotech marketer",
                "nanotech marketer",
                "blockchain marketer",
                "crypto marketer",
                "nft marketer",
                "defi marketer",
                "web3 marketer",
                "metaverse marketer",
                "ar marketer",
                "vr marketer",
                "ai marketer",
                "ml marketer",
                "data marketer",
                "analytics marketer",
                "insights marketer",
                "research marketer",
                "strategy marketer",
                "planning marketer",
                "execution marketer",
                "implementation marketer",
                "delivery marketer",
                "achievement marketer",
                "success marketer",
                "excellence marketer",
                "quality marketer",
                "perfection marketer",
                "mastery marketer",
                "expertise marketer",
                "specialization marketer",
                "focus marketer",
                "niche marketer",
                "domain marketer",
                "field marketer",
                "area marketer",
                "sector marketer",
                "industry marketer",
                "market marketer",
                "segment marketer",
                "category marketer",
                "vertical marketer",
                "horizontal marketer",
                "cross-functional marketer",
                "multi-disciplinary marketer",
                "interdisciplinary marketer",
                "holistic marketer",
                "comprehensive marketer",
                "complete marketer",
                "total marketer",
                "full marketer",
                "entire marketer",
                "whole marketer",
                "integrated marketer",
                "unified marketer",
                "consolidated marketer",
                "centralized marketer",
                "coordinated marketer",
                "synchronized marketer",
                "aligned marketer",
                "harmonized marketer",
                "balanced marketer",
                "optimized marketer",
                "maximized marketer",
                "enhanced marketer",
                "improved marketer",
                "advanced marketer",
                "evolved marketer",
                "transformed marketer",
                "revolutionized marketer",
                "disrupted marketer",
                "innovated marketer",
                "created marketer",
                "invented marketer",
                "designed marketer",
                "developed marketer",
                "built marketer",
                "constructed marketer",
                "established marketer",
                "founded marketer",
                "launched marketer",
                "started marketer",
                "initiated marketer",
                "began marketer",
                "commenced marketer",
                "originated marketer",
                "pioneered marketer",
                "trailblazed marketer",
                "led marketer",
                "guided marketer",
                "directed marketer",
                "managed marketer",
                "supervised marketer",
                "oversaw marketer",
                "governed marketer",
                "administered marketer",
                "coordinated marketer",
                "organized marketer",
                "planned marketer",
                "strategized marketer",
                "executed marketer",
                "implemented marketer",
                "delivered marketer",
                "achieved marketer",
                "succeeded marketer",
                "excelled marketer",
                "mastered marketer",
                "perfected marketer",
                "optimized marketer",
                "maximized marketer",
                "enhanced marketer",
                "improved marketer",
                "advanced marketer",
                "evolved marketer",
                "transformed marketer",
                "revolutionized marketer",
                "disrupted marketer",
                "innovated marketer",
                "created marketer",
                "invented marketer",
                "designed marketer",
                "developed marketer",
                "built marketer",
                "constructed marketer",
                "established marketer",
                "founded marketer",
                "launched marketer",
                "started marketer",
                "initiated marketer",
                "began marketer",
                "commenced marketer",
                "originated marketer",
                "pioneered marketer",
                "trailblazed marketer",
            ],
            "sales": [
                "sales",
                "account manager",
                "business development",
                "sales representative",
                "account executive",
                "sales manager",
                "relationship manager",
                "sales specialist",
                "sales consultant",
                "sales advisor",
                "sales expert",
                "sales professional",
                "sales executive",
                "sales director",
                "sales lead",
                "sales coordinator",
                "sales assistant",
                "sales associate",
                "sales agent",
                "sales rep",
                "sales person",
                "salesperson",
                "sales team member",
                "sales team lead",
                "sales team manager",
                "sales team director",
                "sales team coordinator",
                "sales team specialist",
                "sales team consultant",
                "sales team advisor",
                "sales team expert",
                "sales team professional",
                "sales team executive",
                "sales team associate",
                "sales team agent",
                "sales team rep",
                "sales team representative",
                "sales development representative",
                "sdr",
                "business development representative",
                "bdr",
                "account development representative",
                "adr",
                "lead development representative",
                "ldr",
                "inside sales representative",
                "outside sales representative",
                "field sales representative",
                "territory sales representative",
                "regional sales representative",
                "national sales representative",
                "international sales representative",
                "global sales representative",
                "enterprise sales representative",
                "corporate sales representative",
                "b2b sales representative",
                "b2c sales representative",
                "b2g sales representative",
                "channel sales representative",
                "partner sales representative",
                "reseller sales representative",
                "distributor sales representative",
                "dealer sales representative",
                "agent sales representative",
                "broker sales representative",
                "consultant sales representative",
                "advisor sales representative",
                "specialist sales representative",
                "expert sales representative",
                "professional sales representative",
                "executive sales representative",
                "director sales representative",
                "manager sales representative",
                "lead sales representative",
                "senior sales representative",
                "junior sales representative",
                "entry level sales representative",
                "experienced sales representative",
                "seasoned sales representative",
                "veteran sales representative",
                "skilled sales representative",
                "talented sales representative",
                "gifted sales representative",
                "exceptional sales representative",
                "outstanding sales representative",
                "excellent sales representative",
                "superior sales representative",
                "premium sales representative",
                "top sales representative",
                "elite sales representative",
                "world class sales representative",
                "best in class sales representative",
                "industry leading sales representative",
                "market leading sales representative",
                "award winning sales representative",
                "recognized sales representative",
                "certified sales representative",
                "licensed sales representative",
                "qualified sales representative",
                "trained sales representative",
                "educated sales representative",
                "experienced sales representative",
                "knowledgeable sales representative",
                "informed sales representative",
                "aware sales representative",
                "conscious sales representative",
                "mindful sales representative",
                "present sales representative",
                "focused sales representative",
                "attentive sales representative",
                "concentrated sales representative",
                "dedicated sales representative",
                "committed sales representative",
                "passionate sales representative",
                "enthusiastic sales representative",
                "energetic sales representative",
                "driven sales representative",
                "motivated sales representative",
                "inspired sales representative",
                "visionary sales representative",
                "purposeful sales representative",
                "mission driven sales representative",
                "values driven sales representative",
                "principle driven sales representative",
                "belief driven sales representative",
                "conviction driven sales representative",
                "standard driven sales representative",
                "ethics driven sales representative",
                "integrity driven sales representative",
                "honest sales representative",
                "transparent sales representative",
                "authentic sales representative",
                "genuine sales representative",
                "sincere sales representative",
                "trustworthy sales representative",
                "reliable sales representative",
                "dependable sales representative",
                "consistent sales representative",
                "stable sales representative",
                "predictable sales representative",
                "certain sales representative",
                "confident sales representative",
                "assured sales representative",
                "secure sales representative",
                "safe sales representative",
                "protected sales representative",
                "caring sales representative",
                "supportive sales representative",
                "helpful sales representative",
                "assistive sales representative",
                "guiding sales representative",
                "directing sales representative",
                "leading sales representative",
                "managing sales representative",
                "supervising sales representative",
                "overseeing sales representative",
                "governing sales representative",
                "administering sales representative",
                "coordinating sales representative",
                "organizing sales representative",
                "planning sales representative",
                "strategizing sales representative",
                "executing sales representative",
                "implementing sales representative",
                "delivering sales representative",
                "achieving sales representative",
                "succeeding sales representative",
                "excelling sales representative",
                "mastering sales representative",
                "perfecting sales representative",
                "optimizing sales representative",
                "maximizing sales representative",
                "enhancing sales representative",
                "improving sales representative",
                "advancing sales representative",
                "evolving sales representative",
                "transforming sales representative",
                "revolutionizing sales representative",
                "disrupting sales representative",
                "innovating sales representative",
                "creating sales representative",
                "inventing sales representative",
                "designing sales representative",
                "developing sales representative",
                "building sales representative",
                "constructing sales representative",
                "establishing sales representative",
                "founding sales representative",
                "launching sales representative",
                "starting sales representative",
                "initiating sales representative",
                "beginning sales representative",
                "commencing sales representative",
                "originating sales representative",
                "pioneering sales representative",
                "trailblazing sales representative",
                "key account manager",
                "major account manager",
                "strategic account manager",
                "global account manager",
                "national account manager",
                "regional account manager",
                "territory account manager",
                "enterprise account manager",
                "corporate account manager",
                "channel account manager",
                "partner account manager",
                "reseller account manager",
                "distributor account manager",
                "dealer account manager",
                "agent account manager",
                "broker account manager",
                "consultant account manager",
                "advisor account manager",
                "specialist account manager",
                "expert account manager",
                "professional account manager",
                "executive account manager",
                "director account manager",
                "manager account manager",
                "lead account manager",
                "senior account manager",
                "junior account manager",
                "entry level account manager",
                "experienced account manager",
                "seasoned account manager",
                "veteran account manager",
                "skilled account manager",
                "talented account manager",
                "gifted account manager",
                "exceptional account manager",
                "outstanding account manager",
                "excellent account manager",
                "superior account manager",
                "premium account manager",
                "top account manager",
                "elite account manager",
                "world class account manager",
                "best in class account manager",
                "industry leading account manager",
                "market leading account manager",
                "award winning account manager",
                "recognized account manager",
                "certified account manager",
                "licensed account manager",
                "qualified account manager",
                "trained account manager",
                "educated account manager",
                "experienced account manager",
                "knowledgeable account manager",
                "informed account manager",
                "aware account manager",
                "conscious account manager",
                "mindful account manager",
                "present account manager",
                "focused account manager",
                "attentive account manager",
                "concentrated account manager",
                "dedicated account manager",
                "committed account manager",
                "passionate account manager",
                "enthusiastic account manager",
                "energetic account manager",
                "driven account manager",
                "motivated account manager",
                "inspired account manager",
                "visionary account manager",
                "purposeful account manager",
                "mission driven account manager",
                "values driven account manager",
                "principle driven account manager",
                "belief driven account manager",
                "conviction driven account manager",
                "standard driven account manager",
                "ethics driven account manager",
                "integrity driven account manager",
                "honest account manager",
                "transparent account manager",
                "authentic account manager",
                "genuine account manager",
                "sincere account manager",
                "trustworthy account manager",
                "reliable account manager",
                "dependable account manager",
                "consistent account manager",
                "stable account manager",
                "predictable account manager",
                "certain account manager",
                "confident account manager",
                "assured account manager",
                "secure account manager",
                "safe account manager",
                "protected account manager",
                "caring account manager",
                "supportive account manager",
                "helpful account manager",
                "assistive account manager",
                "guiding account manager",
                "directing account manager",
                "leading account manager",
                "managing account manager",
                "supervising account manager",
                "overseeing account manager",
                "governing account manager",
                "administering account manager",
                "coordinating account manager",
                "organizing account manager",
                "planning account manager",
                "strategizing account manager",
                "executing account manager",
                "implementing account manager",
                "delivering account manager",
                "achieving account manager",
                "succeeding account manager",
                "excelling account manager",
                "mastering account manager",
                "perfecting account manager",
                "optimizing account manager",
                "maximizing account manager",
                "enhancing account manager",
                "improving account manager",
                "advancing account manager",
                "evolving account manager",
                "transforming account manager",
                "revolutionizing account manager",
                "disrupting account manager",
                "innovating account manager",
                "creating account manager",
                "inventing account manager",
                "designing account manager",
                "developing account manager",
                "building account manager",
                "constructing account manager",
                "establishing account manager",
                "founding account manager",
                "launching account manager",
                "starting account manager",
                "initiating account manager",
                "beginning account manager",
                "commencing account manager",
                "originating account manager",
                "pioneering account manager",
                "trailblazing account manager",
                "business development manager",
                "business development executive",
                "business development director",
                "business development lead",
                "business development coordinator",
                "business development specialist",
                "business development consultant",
                "business development advisor",
                "business development expert",
                "business development professional",
                "business development associate",
                "business development agent",
                "business development rep",
                "business development representative",
                "business development team member",
                "business development team lead",
                "business development team manager",
                "business development team director",
                "business development team coordinator",
                "business development team specialist",
                "business development team consultant",
                "business development team advisor",
                "business development team expert",
                "business development team professional",
                "business development team associate",
                "business development team agent",
                "business development team rep",
                "business development team representative",
                "new business development",
                "existing business development",
                "strategic business development",
                "tactical business development",
                "operational business development",
                "commercial business development",
                "corporate business development",
                "enterprise business development",
                "startup business development",
                "scale up business development",
                "growth business development",
                "expansion business development",
                "international business development",
                "global business development",
                "regional business development",
                "national business development",
                "local business development",
                "domestic business development",
                "overseas business development",
                "cross border business development",
                "multi market business development",
                "multi channel business development",
                "multi product business development",
                "multi service business development",
                "multi solution business development",
                "multi platform business development",
                "multi technology business development",
                "multi industry business development",
                "multi sector business development",
                "multi vertical business development",
                "multi horizontal business development",
                "multi functional business development",
                "multi disciplinary business development",
                "interdisciplinary business development",
                "cross functional business development",
                "holistic business development",
                "comprehensive business development",
                "complete business development",
                "total business development",
                "full business development",
                "entire business development",
                "whole business development",
                "integrated business development",
                "unified business development",
                "consolidated business development",
                "centralized business development",
                "coordinated business development",
                "synchronized business development",
                "aligned business development",
                "harmonized business development",
                "balanced business development",
                "optimized business development",
                "maximized business development",
                "enhanced business development",
                "improved business development",
                "advanced business development",
                "evolved business development",
                "transformed business development",
                "revolutionized business development",
                "disrupted business development",
                "innovated business development",
                "created business development",
                "invented business development",
                "designed business development",
                "developed business development",
                "built business development",
                "constructed business development",
                "established business development",
                "founded business development",
                "launched business development",
                "started business development",
                "initiated business development",
                "began business development",
                "commenced business development",
                "originated business development",
                "pioneered business development",
                "trailblazed business development",
                "led business development",
                "guided business development",
                "directed business development",
                "managed business development",
                "supervised business development",
                "oversaw business development",
                "governed business development",
                "administered business development",
                "coordinated business development",
                "organized business development",
                "planned business development",
                "strategized business development",
                "executed business development",
                "implemented business development",
                "delivered business development",
                "achieved business development",
                "succeeded business development",
                "excelled business development",
                "mastered business development",
                "perfected business development",
                "optimized business development",
                "maximized business development",
                "enhanced business development",
                "improved business development",
                "advanced business development",
                "evolved business development",
                "transformed business development",
                "revolutionized business development",
                "disrupted business development",
                "innovated business development",
                "created business development",
                "invented business development",
                "designed business development",
                "developed business development",
                "built business development",
                "constructed business development",
                "established business development",
                "founded business development",
                "launched business development",
                "started business development",
                "initiated business development",
                "began business development",
                "commenced business development",
                "originated business development",
                "pioneered business development",
                "trailblazed business development",
            ],
            "healthcare": [
                "nurse",
                "doctor",
                "physician",
                "therapist",
                "medical",
                "healthcare",
                "pharmacist",
                "dentist",
                "surgeon",
                "technician",
            ],
            "education": [
                "teacher",
                "instructor",
                "professor",
                "educator",
                "tutor",
                "lecturer",
                "trainer",
                "coordinator",
                "administrator",
            ],
        }

        # Common skill synonyms for better matching
        self.SKILL_SYNONYMS = {
            "javascript": ["js", "javascript", "ecmascript"],
            "typescript": ["ts", "typescript"],
            "react": ["react", "reactjs", "react.js"],
            "vue": ["vue", "vuejs", "vue.js"],
            "angular": ["angular", "angularjs"],
            "node": ["node", "nodejs", "node.js"],
            "python": ["python", "py"],
            "machine learning": [
                "ml",
                "machine learning",
                "ai",
                "artificial intelligence",
            ],
            "data science": ["data science", "data analytics", "analytics"],
            "project management": ["pm", "project management", "agile", "scrum"],
        }

    def search_jobs_for_user(self, user_id: int, limit: int = 100) -> List[Dict]:
        """Advanced job search using multiple intelligent matching strategies"""
        try:
            # Get user preferences
            cursor = self.connection.cursor(
                cursor_factory=psycopg2.extras.RealDictCursor
            )
            cursor.execute(
                "SELECT * FROM user_preferences WHERE user_id = %s", (user_id,)
            )
            prefs = cursor.fetchone()

            if not prefs:
                logger.info(f"No preferences found for user {user_id}")
                return []

            prefs = dict(prefs)
            logger.info(f"🔍 Intelligent job search for user {user_id}")

            # Get all recent jobs for matching (from canonical_jobs table)
            cursor.execute(
                """
                SELECT
                    id, title, company, location, description, job_url, source,
                    ai_salary_min as salary_min, ai_salary_max as salary_max,
                    ai_salary_currency as salary_currency,
                    ai_employment_type as employment_type,
                    ai_remote_allowed as is_remote,
                    posted_date,

                    -- Contact Information (CRITICAL for CTA buttons)
                    email, ai_email, whatsapp_number, ai_whatsapp_number,

                    -- AI Enhanced Fields for Better Matching
                    ai_job_titles,  -- Full array of job title variations
                    ai_job_function,  -- Sales, Engineering, Marketing, etc.
                    ai_job_level,  -- Entry-level, Mid-level, Senior, etc.
                    ai_industry,  -- Technology, Healthcare, Finance, etc.
                    ai_skills_required,  -- Required skills array
                    ai_years_experience_min,
                    ai_years_experience_max,
                    ai_work_arrangement,  -- Remote, On-site, Hybrid
                    ai_remote_allowed,

                    -- Fallback fields
                    CASE WHEN ai_job_titles IS NOT NULL AND array_length(ai_job_titles, 1) > 0
                         THEN ai_job_titles[1]
                         ELSE title
                    END as ai_job_title,
                    job_url as ai_application_url,
                    ai_summary as whatsapp_summary
                FROM canonical_jobs
                WHERE posted_date >= CURRENT_DATE - INTERVAL '60 days'
                   OR posted_date IS NULL
                ORDER BY
                    CASE WHEN ai_summary IS NOT NULL THEN 0 ELSE 1 END,
                    -- Balanced sorting to ensure WhatsApp jobs aren't pushed out by more frequent JobSpy scraping
                    CASE
                        WHEN source = 'whatsapp' THEN scraped_at + INTERVAL '1 day'  -- Boost WhatsApp jobs
                        ELSE scraped_at
                    END DESC NULLS FIRST,
                    id DESC  -- Add deterministic secondary sort
                LIMIT 2000  -- Increased limit to ensure WhatsApp jobs are included
            """
            )
            all_jobs = cursor.fetchall()

            if not all_jobs:
                logger.info("No recent jobs found in database")
                return []

            # Score each job using multiple strategies
            scored_jobs = []
            for job in all_jobs:
                job_dict = dict(job)
                score = self._calculate_job_score(prefs, job_dict)
                if score >= 50.0:  # Only include jobs with 50%+ match
                    job_dict["match_score"] = score
                    job_dict["match_reasons"] = self._get_match_reasons(prefs, job_dict)
                    scored_jobs.append(job_dict)

            # Sort by score and return top matches
            scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
            top_jobs = scored_jobs[:limit]

            logger.info(
                f"🎯 Found {len(top_jobs)} intelligent matches for user {user_id}"
            )
            return top_jobs

        except Exception as e:
            logger.error(f"❌ Error in intelligent job search: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return []

    def _calculate_job_score(self, user_prefs: Dict, job: Dict) -> float:
        """
        Calculate AI-enhanced job match score using multiple intelligent strategies

        ENHANCED SCORING SYSTEM (Total: 102 points, capped at 100):
        ================================================================
        1. AI Job Titles (35 pts)     - Fuzzy matching with 15+ AI variations
        2. Work Arrangement (20 pts)   - Remote/hybrid/onsite with AI detection
        3. Salary Matching (20 pts)    - Currency conversion & range flexibility
        4. Experience Level (10 pts)   - AI years + level hierarchy matching
        5. AI Job Function (7 pts)     - Semantic function classification
        6. AI Industry (5 pts)         - Industry category matching
        7. Semantic Clusters (5 pts)   - Fallback fuzzy matching
        8. Skills Matching (0 pts)     - DISABLED for now
        9. Contact Info Bonus (0 pts)  - DISABLED for now

        LOCATION FILTERING (Not Scored):
        - Location works as a FILTER, not scoring
        - Jobs that don't match user's preferred_locations are excluded
        - Intelligent abbreviation handling (Lagos/LOS, Abuja/FCT, PH, etc.)
        - Geographic proximity for Nigerian cities and states

        Key Enhancements:
        - Uses AI-enhanced fields (ai_city, ai_remote_allowed, ai_salary_*, etc.)
        - Location filtering with abbreviation intelligence
        - Currency conversion with flexible salary ranges
        - Required vs preferred skills distinction
        - Experience level hierarchy with flexibility
        - Work arrangement intelligent detection
        """

        # LOCATION FILTERING - Apply before scoring
        if not self._is_location_compatible(user_prefs, job):
            return 0.0  # Exclude jobs that don't match location preferences

        total_score = 0.0

        # 1. AI JOB TITLES MATCHING (35 points) - Enhanced with 15+ AI variations
        ai_title_score = self._score_ai_job_titles_match(user_prefs, job)
        total_score += ai_title_score

        # 2. WORK ARRANGEMENT MATCHING (20 points) - Enhanced with AI detection
        work_score = self._score_work_arrangement(user_prefs, job)
        total_score += work_score

        # 3. SALARY MATCHING (20 points) - Enhanced with currency conversion
        salary_score = self._score_salary_match(user_prefs, job)
        total_score += salary_score

        # 4. EXPERIENCE LEVEL MATCHING (10 points) - Enhanced with AI fields
        exp_score = self._score_experience_match(user_prefs, job)
        total_score += exp_score

        # 5. AI JOB FUNCTION MATCHING (7 points) - Reduced weight
        function_score = self._score_ai_job_function_match(user_prefs, job)
        total_score += function_score * 0.28  # Scale from 25 to 7 points

        # 6. AI INDUSTRY MATCHING (5 points) - Reduced weight
        industry_score = self._score_ai_industry_match(user_prefs, job)
        total_score += industry_score * 0.25  # Scale from 20 to 5 points

        # 7. SEMANTIC CLUSTER MATCHING (5 points) - Low weight fallback
        cluster_score = self._score_semantic_clusters(user_prefs, job)
        total_score += cluster_score * 0.2  # Scale from 25 to 5 points

        # 8. SKILLS MATCHING (0 points) - DISABLED for now
        # skills_score = self._score_skills_match(user_prefs, job)
        # total_score += skills_score

        # 9. CONTACT INFORMATION BONUS (0 points) - DISABLED for now
        # contact_score = self._score_contact_availability(job)
        # total_score += contact_score

        return min(total_score, 100.0)  # Cap at 100%

    def _is_location_compatible(self, user_prefs: Dict, job: Dict) -> bool:
        """
        LOCATION FILTERING - Determine if job location matches user preferences

        This is a FILTER, not scoring. Jobs that don't match are excluded entirely.

        Compares:
        - user_prefs['preferred_locations'] vs job['location'], job['ai_city'], job['ai_state']
        - Handles abbreviations: Lagos/LOS, Abuja/FCT, Port Harcourt/PH, etc.
        - Geographic proximity for Nigerian locations
        - Remote work exceptions

        CRITICAL FIX: Always allow remote jobs if they're truly remote, regardless of user preferences
        """
        user_locations = user_prefs.get("preferred_locations", []) or []
        willing_to_relocate = user_prefs.get("willing_to_relocate", False)
        user_work_arrangements = user_prefs.get("work_arrangements", []) or []

        # CRITICAL FIX: Always allow remote jobs if they're truly remote
        # This fixes the issue where data science remote jobs were being filtered out
        if self._job_allows_remote_work(job):
            return True  # Remote jobs should always be allowed

        # If no location preferences set, allow all jobs
        if not user_locations:
            return True

        # If user wants remote work, check if job allows remote (already handled above)
        if "remote" in [arr.lower() for arr in user_work_arrangements]:
            if self._job_allows_remote_work(job):
                return True  # Remote jobs bypass location filtering

        # If user is willing to relocate, allow all jobs with valid locations
        if willing_to_relocate:
            job_location = job.get("location", "").strip()
            ai_city = job.get("ai_city", "").strip()
            ai_country = job.get("ai_country", "").strip()
            if job_location or ai_city or ai_country:
                return True

        # Get job location data
        job_location = (job.get("location", "") or "").lower().strip()
        ai_city = (job.get("ai_city", "") or "").lower().strip()
        ai_state = (job.get("ai_state", "") or "").lower().strip()
        ai_country = (job.get("ai_country", "") or "").lower().strip()

        # Check each user preferred location
        for user_location in user_locations:
            user_loc_lower = user_location.lower().strip()

            if self._locations_match(
                user_loc_lower, job_location, ai_city, ai_state, ai_country
            ):
                return True

        return False

    def _job_allows_remote_work(self, job: Dict) -> bool:
        """Check if job allows remote work - prioritize AI fields over text"""
        # AI-enhanced remote detection (highest priority)
        ai_remote_allowed = job.get("ai_remote_allowed")
        ai_work_arrangement = (job.get("ai_work_arrangement", "") or "").lower()

        # If AI fields are available, use them exclusively
        if ai_remote_allowed is not None or ai_work_arrangement:
            if ai_remote_allowed or "remote" in ai_work_arrangement:
                return True
            else:
                return False  # AI says not remote, don't check text

        # Legacy remote detection (fallback)
        is_remote = job.get("is_remote", False)
        if is_remote:
            return True

        # Text-based remote detection (only if no AI data available)
        job_title = (job.get("title", "") or "").lower()
        job_description = (job.get("description", "") or "").lower()
        location = (job.get("location", "") or "").lower()

        remote_keywords = [
            "remote",
            "work from home",
            "wfh",
            "telecommute",
            "distributed",
        ]
        all_text = f"{job_title} {job_description} {location}"

        return any(keyword in all_text for keyword in remote_keywords)

    def _locations_match(
        self,
        user_location: str,
        job_location: str,
        ai_city: str,
        ai_state: str,
        ai_country: str,
    ) -> bool:
        """
        Intelligent location matching with abbreviation handling

        Handles:
        - Direct matches
        - Nigerian abbreviations (Lagos/LOS, Abuja/FCT, PH, etc.)
        - State-level matching
        - City variations and proximity
        - International locations
        """
        # Extract key location terms from user input
        user_terms = self._extract_location_terms(user_location)

        # Direct exact matches (original logic)
        if (
            user_location in job_location
            or user_location in ai_city
            or user_location in ai_state
        ):
            return True

        # Flexible partial matching - check if any user term matches job location
        all_job_location_text = f"{job_location} {ai_city} {ai_state}".lower()
        for term in user_terms:
            if term in all_job_location_text:
                return True

        # Nigerian location abbreviations and variations
        if self._nigerian_location_match(
            user_location, job_location, ai_city, ai_state
        ):
            return True

        # International location matching
        if self._international_location_match(
            user_location, job_location, ai_city, ai_country
        ):
            return True

        # Geographic proximity for Nigerian cities
        if self._nigerian_proximity_match(user_location, ai_city, ai_state):
            return True

        return False

    def _extract_location_terms(self, location: str) -> list:
        """
        Extract key location terms from user location input

        Examples:
        - "Lagos, Lagos State" → ["lagos", "lagos state"]
        - "Abuja, FCT" → ["abuja", "fct"]
        - "Port Harcourt" → ["port harcourt", "port", "harcourt"]
        """
        if not location:
            return []

        location_lower = location.lower().strip()
        terms = []

        # Split by common separators
        parts = location_lower.replace(",", " ").replace("-", " ").split()

        # Add individual words
        for part in parts:
            if len(part) > 2:  # Skip very short words
                terms.append(part)

        # Add the full location
        terms.append(location_lower)

        # Add combinations for multi-word locations
        if len(parts) > 1:
            # Add pairs of words
            for i in range(len(parts) - 1):
                pair = f"{parts[i]} {parts[i+1]}"
                terms.append(pair)

        # Remove duplicates and return
        return list(set(terms))

    def _nigerian_location_match(
        self, user_location: str, job_location: str, ai_city: str, ai_state: str
    ) -> bool:
        """Handle Nigerian location abbreviations and variations"""

        # Nigerian location mappings with abbreviations
        nigerian_locations = {
            # Lagos variations
            "lagos": [
                "lagos",
                "los",
                "lagos state",
                "lagos island",
                "lagos mainland",
                "ikeja",
                "victoria island",
                "vi",
                "ikoyi",
                "lekki",
                "surulere",
                "yaba",
            ],
            "los": ["lagos", "los", "lagos state"],
            # Abuja variations
            "abuja": [
                "abuja",
                "fct",
                "federal capital territory",
                "garki",
                "wuse",
                "maitama",
                "asokoro",
                "gwarinpa",
            ],
            "fct": ["abuja", "fct", "federal capital territory"],
            # Port Harcourt variations
            "port harcourt": [
                "port harcourt",
                "ph",
                "portharcourt",
                "rivers",
                "rivers state",
            ],
            "ph": ["port harcourt", "ph", "portharcourt", "rivers"],
            # Other major cities
            "kano": ["kano", "kano state"],
            "ibadan": ["ibadan", "oyo", "oyo state"],
            "kaduna": ["kaduna", "kaduna state"],
            "jos": ["jos", "plateau", "plateau state"],
            "enugu": ["enugu", "enugu state"],
            "calabar": ["calabar", "cross river", "cross river state"],
            "warri": ["warri", "delta", "delta state"],
            "benin": ["benin", "benin city", "edo", "edo state"],
            "aba": ["aba", "abia", "abia state"],
            "onitsha": ["onitsha", "anambra", "anambra state"],
        }

        # Check if user location matches any variation
        user_variations = []
        for main_location, variations in nigerian_locations.items():
            if user_location in variations:
                user_variations = variations
                break

        if not user_variations:
            user_variations = [user_location]  # Use as-is if no mapping found

        # Check against job location fields
        all_job_text = f"{job_location} {ai_city} {ai_state}".lower()

        return any(variation in all_job_text for variation in user_variations)

    def _international_location_match(
        self, user_location: str, job_location: str, ai_city: str, ai_country: str
    ) -> bool:
        """Handle international location matching"""

        # Country-level matching
        country_mappings = {
            "nigeria": ["nigeria", "ng", "nigerian", "naija"],
            "ghana": ["ghana", "gh", "ghanaian"],
            "kenya": ["kenya", "ke", "kenyan", "nairobi"],
            "south africa": ["south africa", "za", "sa", "cape town", "johannesburg"],
            "united states": ["usa", "us", "united states", "america", "american"],
            "united kingdom": [
                "uk",
                "united kingdom",
                "britain",
                "british",
                "england",
                "london",
            ],
            "canada": ["canada", "ca", "canadian", "toronto", "vancouver"],
            "germany": ["germany", "de", "german", "berlin", "munich"],
            "france": ["france", "fr", "french", "paris"],
        }

        # Find user's country group
        user_country_variations = []
        for country, variations in country_mappings.items():
            if user_location in variations:
                user_country_variations = variations
                break

        if user_country_variations:
            all_job_text = f"{job_location} {ai_city} {ai_country}".lower()
            return any(
                variation in all_job_text for variation in user_country_variations
            )

        return False

    def _nigerian_proximity_match(
        self, user_location: str, ai_city: str, ai_state: str
    ) -> bool:
        """Check for geographic proximity within Nigerian regions - STRICT matching only"""

        # Regional clusters for proximity matching - ONLY same region allowed
        regional_clusters = {
            "southwest": [
                "lagos",
                "ibadan",
                "abeokuta",
                "ilorin",
                "oshogbo",
                "akure",
                "ado ekiti",
            ],
            "southeast": [
                "enugu",
                "onitsha",
                "aba",
                "owerri",
                "umuahia",
                "awka",
                "abakaliki",
            ],
            "southsouth": [
                "port harcourt",
                "warri",
                "benin",
                "calabar",
                "uyo",
                "yenagoa",
            ],
            "northcentral": ["abuja", "jos", "makurdi", "minna", "lokoja", "lafia"],
            "northwest": ["kano", "kaduna", "zaria", "sokoto", "katsina"],
            "northeast": ["maiduguri", "yola", "bauchi", "gombe", "jalingo"],
        }

        # Find user's region
        user_region = None
        for region, cities in regional_clusters.items():
            if any(city in user_location for city in cities):
                user_region = region
                break

        if not user_region:
            return False

        # Find job's region
        job_region = None
        ai_city_lower = ai_city.lower()
        for region, cities in regional_clusters.items():
            if any(city in ai_city_lower for city in cities):
                job_region = region
                break

        # Only allow matches within the SAME region (strict proximity)
        return user_region == job_region and job_region is not None

    def _score_ai_job_titles_match(self, user_prefs: dict, job: dict) -> float:
        """
        Enhanced job title matching using ALL available fields with intelligent weighting

        User Fields:
        - job_categories[] (high-level: technology, healthcare, etc.)
        - job_roles[] (specific: frontend developer, data analyst, etc.)
        - user_job_input (verbatim: "I want to be a Python developer")

        Job Fields:
        - ai_job_titles[] (AI-generated 15+ variations)
        - title (original job title)
        """
        # Get all user job-related data
        user_categories = user_prefs.get("job_categories", []) or []
        user_roles = user_prefs.get("job_roles", []) or []
        user_job_input = user_prefs.get("user_job_input", "") or ""

        # If no job preferences at all, return 0
        if not user_categories and not user_roles and not user_job_input:
            return 0.0

        # Get job title data
        ai_job_titles = job.get("ai_job_titles", []) or []
        job_title = job.get("title", "").lower()

        max_score = 0.0

        # 1. EXACT MATCHES IN AI JOB TITLES (35 points - highest priority)
        max_score = max(
            max_score,
            self._score_exact_ai_title_matches(
                user_roles, user_job_input, ai_job_titles
            ),
        )

        # 2. FUZZY MATCHES IN AI JOB TITLES (25-30 points)
        if max_score < 35.0:
            max_score = max(
                max_score,
                self._score_fuzzy_ai_title_matches(
                    user_roles, user_job_input, ai_job_titles
                ),
            )

        # 3. CATEGORY-LEVEL MATCHES (20 points)
        if max_score < 30.0:
            max_score = max(
                max_score,
                self._score_category_title_matches(
                    user_categories, ai_job_titles, job_title
                ),
            )

        # 4. ORIGINAL TITLE FALLBACK (15 points)
        if max_score < 20.0:
            max_score = max(
                max_score,
                self._score_original_title_matches(
                    user_roles, user_job_input, job_title
                ),
            )

        # 5. SEMANTIC KEYWORD MATCHING (10 points)
        if max_score < 15.0:
            max_score = max(
                max_score,
                self._score_semantic_title_matches(
                    user_job_input, ai_job_titles, job_title
                ),
            )

        return max_score

    def _score_exact_ai_title_matches(
        self, user_roles: list, user_job_input: str, ai_job_titles: list
    ) -> float:
        """Score exact matches in AI job titles (35 points)"""
        if not ai_job_titles:
            return 0.0

        # Check user_roles first (processed/standardized)
        for user_role in user_roles:
            if not user_role:
                continue
            user_role_lower = user_role.lower()

            for ai_title in ai_job_titles:
                if ai_title and user_role_lower in ai_title.lower():
                    return 35.0  # Perfect match

        # Check user_job_input (verbatim user text)
        if user_job_input:
            user_input_lower = user_job_input.lower()

            # Extract key terms from user input
            key_terms = self._extract_job_keywords(user_input_lower)

            for ai_title in ai_job_titles:
                if not ai_title:
                    continue
                ai_title_lower = ai_title.lower()

                # Check if multiple key terms match
                matching_terms = sum(1 for term in key_terms if term in ai_title_lower)
                if matching_terms >= 2:  # At least 2 key terms match
                    return 35.0
                elif (
                    matching_terms == 1 and len(key_terms) == 1
                ):  # Single term perfect match
                    return 35.0

        return 0.0

    def _score_fuzzy_ai_title_matches(
        self, user_roles: list, user_job_input: str, ai_job_titles: list
    ) -> float:
        """Score fuzzy matches in AI job titles (25-30 points)"""
        if not ai_job_titles:
            return 0.0

        max_score = 0.0

        # Check user_roles with fuzzy matching (enhanced for sales)
        for user_role in user_roles:
            if not user_role:
                continue
            user_role_lower = user_role.lower()

            for ai_title in ai_job_titles:
                if not ai_title:
                    continue
                ai_title_lower = ai_title.lower()

                # Special handling for sales-related titles
                if "sales" in user_role_lower and "sales" in ai_title_lower:
                    # Sales Manager vs Sales Executive should score highly
                    sales_terms = [
                        "manager",
                        "executive",
                        "supervisor",
                        "representative",
                        "associate",
                        "specialist",
                        "coordinator",
                        "lead",
                    ]
                    user_has_sales_term = any(
                        term in user_role_lower for term in sales_terms
                    )
                    job_has_sales_term = any(
                        term in ai_title_lower for term in sales_terms
                    )

                    if user_has_sales_term and job_has_sales_term:
                        max_score = max(
                            max_score, 32.0
                        )  # High score for sales variations
                    elif "sales" in user_role_lower and "sales" in ai_title_lower:
                        max_score = max(
                            max_score, 30.0
                        )  # Good score for any sales match

                # Regular fuzzy matching
                similarity = SequenceMatcher(
                    None, user_role_lower, ai_title_lower
                ).ratio()
                if similarity > 0.85:
                    max_score = max(max_score, 30.0)
                elif similarity > 0.7:
                    max_score = max(max_score, 25.0)
                elif similarity > 0.6 and "sales" in user_role_lower:
                    # More lenient for sales roles
                    max_score = max(max_score, 22.0)

        # Check user_job_input with fuzzy matching
        if user_job_input and max_score < 30.0:
            key_terms = self._extract_job_keywords(user_job_input.lower())

            for ai_title in ai_job_titles:
                if not ai_title:
                    continue
                ai_title_lower = ai_title.lower()

                # Calculate fuzzy match for each key term
                for term in key_terms:
                    similarity = SequenceMatcher(None, term, ai_title_lower).ratio()
                    if similarity > 0.8:
                        max_score = max(max_score, 28.0)
                    elif similarity > 0.6:
                        max_score = max(max_score, 22.0)

        return max_score

    def _score_category_title_matches(
        self, user_categories: list, ai_job_titles: list, job_title: str
    ) -> float:
        """Score category-level matches (20 points)"""
        if not user_categories:
            return 0.0

        # Category to job title mappings
        category_keywords = {
            "technology": [
                "developer",
                "engineer",
                "programmer",
                "software",
                "tech",
                "it",
                "data",
                "analyst",
                "devops",
                "qa",
            ],
            "healthcare": [
                "nurse",
                "doctor",
                "medical",
                "health",
                "clinical",
                "pharmacy",
                "therapy",
            ],
            "finance": [
                "financial",
                "accounting",
                "analyst",
                "banker",
                "investment",
                "audit",
                "controller",
            ],
            "marketing": [
                "marketing",
                "digital",
                "social media",
                "content",
                "brand",
                "campaign",
                "seo",
            ],
            "sales": [
                "sales",
                "business development",
                "account",
                "relationship",
                "revenue",
            ],
            "design": ["designer", "ui", "ux", "graphic", "creative", "visual", "art"],
            "education": [
                "teacher",
                "instructor",
                "professor",
                "tutor",
                "education",
                "training",
            ],
            "operations": [
                "operations",
                "logistics",
                "supply chain",
                "process",
                "coordinator",
            ],
            "human resources": [
                "hr",
                "human resources",
                "recruiter",
                "talent",
                "people",
            ],
            "customer service": [
                "customer",
                "support",
                "service",
                "help desk",
                "call center",
            ],
        }

        for category in user_categories:
            if not category:
                continue
            category_lower = category.lower()

            keywords = category_keywords.get(category_lower, [category_lower])

            # Check AI job titles
            for ai_title in ai_job_titles:
                if ai_title and any(
                    keyword in ai_title.lower() for keyword in keywords
                ):
                    return 20.0

            # Check original job title
            if any(keyword in job_title for keyword in keywords):
                return 20.0

        return 0.0

    def _score_original_title_matches(
        self, user_roles: list, user_job_input: str, job_title: str
    ) -> float:
        """Score matches in original job title (15 points)"""
        if not job_title:
            return 0.0

        # Check user_roles
        for user_role in user_roles:
            if user_role and user_role.lower() in job_title:
                return 15.0

        # Check user_job_input keywords
        if user_job_input:
            key_terms = self._extract_job_keywords(user_job_input.lower())
            matching_terms = sum(1 for term in key_terms if term in job_title)

            if matching_terms >= 2:
                return 15.0
            elif matching_terms == 1 and len(key_terms) == 1:
                return 15.0

        return 0.0

    def _score_semantic_title_matches(
        self, user_job_input: str, ai_job_titles: list, job_title: str
    ) -> float:
        """Score semantic keyword matches (10 points)"""
        if not user_job_input:
            return 0.0

        # Extract semantic keywords from user input
        semantic_keywords = self._extract_semantic_keywords(user_job_input.lower())

        if not semantic_keywords:
            return 0.0

        # Check AI job titles
        for ai_title in ai_job_titles:
            if ai_title and any(
                keyword in ai_title.lower() for keyword in semantic_keywords
            ):
                return 10.0

        # Check original job title
        if any(keyword in job_title for keyword in semantic_keywords):
            return 10.0

        return 0.0

    def _extract_job_keywords(self, text: str) -> list:
        """Extract key job-related terms from user input"""
        # Remove common words and extract meaningful terms
        stop_words = {
            "i",
            "want",
            "to",
            "be",
            "a",
            "an",
            "the",
            "as",
            "for",
            "in",
            "at",
            "with",
            "and",
            "or",
        }

        # Split and clean
        words = text.replace(",", " ").replace(".", " ").split()
        keywords = []

        for word in words:
            word = word.strip().lower()
            if len(word) > 2 and word not in stop_words:
                keywords.append(word)

        # Also extract multi-word phrases
        phrases = []
        if "software developer" in text:
            phrases.append("software developer")
        if "data analyst" in text:
            phrases.append("data analyst")
        if "project manager" in text:
            phrases.append("project manager")
        if "business analyst" in text:
            phrases.append("business analyst")

        return phrases + keywords

    def _extract_semantic_keywords(self, text: str) -> list:
        """Extract semantic keywords that indicate job intent"""
        semantic_map = {
            "python": ["python", "django", "flask"],
            "javascript": ["javascript", "js", "react", "vue", "angular", "node"],
            "data": [
                "data",
                "analytics",
                "analysis",
                "science",
                "scientist",
                "analyst",
                "intelligence",
                "bi",
                "business intelligence",
                "machine learning",
                "ml",
                "ai",
                "artificial intelligence",
                "big data",
                "data mining",
                "data engineer",
                "data engineering",
                "quantitative",
                "statistics",
                "statistical",
                "research",
                "modeling",
                "predictive",
                "data science",
                "data analytics",
            ],
            "web": ["web", "website", "frontend", "backend", "fullstack"],
            "mobile": ["mobile", "android", "ios", "app", "application"],
            "design": ["design", "ui", "ux", "graphic", "visual"],
            "management": ["manager", "management", "lead", "supervisor"],
            "sales": ["sales", "selling", "business development"],
            "marketing": ["marketing", "digital marketing", "social media"],
        }

        keywords = []
        for category, terms in semantic_map.items():
            if any(term in text for term in terms):
                keywords.extend(terms)

        return list(set(keywords))  # Remove duplicates

    def _score_ai_job_function_match(self, user_prefs: dict, job: dict) -> float:
        """Match based on AI job function (Sales, Engineering, etc.)"""
        user_categories = user_prefs.get("job_categories", []) or []
        user_roles = user_prefs.get("job_roles", []) or []

        if not user_categories and not user_roles:
            return 0.0

        ai_job_function = job.get("ai_job_function", "") or ""
        if not ai_job_function:
            return 0.0

        # Handle case where ai_job_function might be a list
        if isinstance(ai_job_function, list):
            ai_job_function = ai_job_function[0] if ai_job_function else ""

        if not ai_job_function:
            return 0.0

        ai_function_lower = ai_job_function.lower()

        # Check user categories first (highest priority)
        for category in user_categories:
            if category and category.lower() in ai_function_lower:
                return 25.0

        # Enhanced direct matching for data roles (second priority - 25 points)
        if user_roles and any(
            "data" in role.lower() or "analyst" in role.lower() for role in user_roles
        ):
            if any(
                keyword in ai_function_lower
                for keyword in ["data", "analytics", "analyst", "intelligence"]
            ):
                return 25.0  # Full points for direct data match

        # Check user roles for function keywords (third priority - 20 points)
        function_keywords = {
            "sales": ["sales", "business development", "account management"],
            "engineering": ["engineer", "developer", "technical", "software"],
            "marketing": ["marketing", "digital marketing", "content"],
            "customer service": ["customer", "support", "service"],
            "finance": ["finance", "accounting", "financial"],
            "hr": ["hr", "human resources", "recruitment"],
            "operations": ["operations", "logistics", "supply chain"],
        }

        if user_roles:
            for user_role in user_roles:
                user_role_lower = user_role.lower()
                for func, keywords in function_keywords.items():
                    if any(keyword in user_role_lower for keyword in keywords):
                        if func in ai_function_lower:
                            return 20.0

        return 0.0

    def _score_ai_industry_match(self, user_prefs: dict, job: dict) -> float:
        """Match based on AI industry classification"""
        user_industries = user_prefs.get("industry_preferences", []) or []
        user_roles = user_prefs.get("job_roles", []) or []

        ai_industries = job.get("ai_industry", []) or []
        if not ai_industries:
            return 0.0

        # Direct industry preference match
        if user_industries:
            for user_industry in user_industries:
                for ai_industry in ai_industries:
                    if (
                        user_industry
                        and ai_industry
                        and user_industry.lower() in ai_industry.lower()
                    ):
                        return 20.0

        # Infer industry from user roles with enhanced sales matching
        role_industry_map = {
            "tech": ["technology", "software", "information technology"],
            "finance": ["finance", "financial services", "banking"],
            "healthcare": ["healthcare", "medical", "pharmaceutical"],
            "education": ["education", "academic", "training"],
            "retail": ["retail", "e-commerce", "consumer goods"],
            "media": ["media", "entertainment", "advertising"],
            "sales": [
                "sales",
                "retail",
                "finance",
                "insurance",
                "real estate",
                "pharmaceutical",
                "healthcare",
                "consulting",
                "business",
            ],
        }

        # Special handling for sales roles - they work across many industries
        sales_keywords = ["sales", "account", "business development", "key account"]
        is_sales_user = user_roles and any(
            keyword in role.lower() for role in user_roles for keyword in sales_keywords
        )

        if is_sales_user:
            # Sales roles are valuable across many industries
            sales_friendly_industries = [
                "healthcare",
                "medical",
                "pharmaceutical",
                "finance",
                "financial",
                "insurance",
                "retail",
                "real estate",
                "consulting",
                "business",
                "technology",
                "software",
                "manufacturing",
                "automotive",
            ]
            for ai_industry in ai_industries:
                ai_industry_lower = ai_industry.lower()
                if any(
                    industry in ai_industry_lower
                    for industry in sales_friendly_industries
                ):
                    return 15.0  # Good match for sales in relevant industries
                elif "sales" in ai_industry_lower:
                    return 20.0  # Perfect match for sales industry

        for user_role in user_roles:
            user_role_lower = user_role.lower()
            for role_key, industries in role_industry_map.items():
                if role_key in user_role_lower:
                    for ai_industry in ai_industries:
                        if any(ind in ai_industry.lower() for ind in industries):
                            return 15.0

        # Fallback: any industry with sales component gets some points
        for ai_industry in ai_industries:
            if "sales" in ai_industry.lower():
                return 10.0

        return 0.0

    def _score_job_titles(self, user_prefs: Dict, job: Dict) -> float:
        """Score exact job title matches"""
        user_roles = user_prefs.get("job_roles", [])
        if not user_roles:
            return 0.0

        # Get job title fields
        job_title = (job.get("title", "") or "").lower()

        # Handle ai_job_title which might be a list
        ai_job_title_raw = job.get("ai_job_title", "") or ""
        if isinstance(ai_job_title_raw, list):
            ai_job_title = ai_job_title_raw[0].lower() if ai_job_title_raw else ""
        else:
            ai_job_title = ai_job_title_raw.lower()

        max_score = 0.0
        for user_role in user_roles:
            user_role_lower = user_role.lower()

            # Exact matches
            if user_role_lower in job_title or user_role_lower in ai_job_title:
                max_score = max(max_score, 40.0)
            # Partial matches
            elif any(word in job_title for word in user_role_lower.split()):
                max_score = max(max_score, 25.0)
            elif any(word in ai_job_title for word in user_role_lower.split()):
                max_score = max(max_score, 20.0)

        return max_score

    def _score_fuzzy_titles(self, user_prefs: Dict, job: Dict) -> float:
        """Score fuzzy job title matches using string similarity"""
        user_roles = user_prefs.get("job_roles", [])
        if not user_roles:
            return 0.0

        job_title = (job.get("title", "") or "").lower()

        # Handle ai_job_title which might be a list
        ai_job_title_raw = job.get("ai_job_title", "") or ""
        if isinstance(ai_job_title_raw, list):
            ai_job_title = ai_job_title_raw[0].lower() if ai_job_title_raw else ""
        else:
            ai_job_title = ai_job_title_raw.lower()

        max_score = 0.0
        for user_role in user_roles:
            user_role_lower = user_role.lower()

            # Calculate similarity ratios
            title_similarity = SequenceMatcher(None, user_role_lower, job_title).ratio()
            ai_title_similarity = SequenceMatcher(
                None, user_role_lower, ai_job_title
            ).ratio()

            # Convert similarity to score (threshold of 0.6 for relevance)
            best_similarity = max(title_similarity, ai_title_similarity)
            if best_similarity >= 0.6:
                fuzzy_score = (
                    (best_similarity - 0.6) / 0.4 * 30.0
                )  # Scale to 0-30 points
                max_score = max(max_score, fuzzy_score)

        return max_score

    def _score_semantic_clusters(self, user_prefs: Dict, job: Dict) -> float:
        """Score semantic cluster matches"""
        user_roles = user_prefs.get("job_roles", [])
        if not user_roles:
            return 0.0

        job_title = (job.get("title", "") or "").lower()

        # Handle ai_job_title which might be a list
        ai_job_title_raw = job.get("ai_job_title", "") or ""
        if isinstance(ai_job_title_raw, list):
            ai_job_title = ai_job_title_raw[0].lower() if ai_job_title_raw else ""
        else:
            ai_job_title = ai_job_title_raw.lower()

        job_description = (job.get("description", "") or "").lower()

        # Find user's clusters
        user_clusters = set()
        for user_role in user_roles:
            user_role_lower = user_role.lower()
            for cluster_name, cluster_terms in self.JOB_CLUSTERS.items():
                if any(term in user_role_lower for term in cluster_terms):
                    user_clusters.add(cluster_name)

        if not user_clusters:
            return 0.0

        # Check if job matches any user clusters
        max_score = 0.0
        for cluster_name in user_clusters:
            cluster_terms = self.JOB_CLUSTERS[cluster_name]

            # Check title matches
            title_matches = sum(
                1 for term in cluster_terms if term in job_title or term in ai_job_title
            )

            # Check description matches (lower weight)
            desc_matches = sum(1 for term in cluster_terms if term in job_description)

            if title_matches > 0:
                cluster_score = min(title_matches * 15.0, 25.0)  # Up to 25 points
                max_score = max(max_score, cluster_score)
            elif desc_matches > 0:
                cluster_score = min(desc_matches * 5.0, 15.0)  # Up to 15 points
                max_score = max(max_score, cluster_score)

        return max_score

    def _score_skills_match(self, user_prefs: Dict, job: Dict) -> float:
        """Enhanced AI-powered skills matching with required/preferred distinction"""
        user_technical_skills = user_prefs.get("technical_skills", []) or []
        user_soft_skills = user_prefs.get("soft_skills", []) or []

        if not user_technical_skills and not user_soft_skills:
            return 0.0

        # Get AI-enhanced skills data
        ai_required_skills = job.get("ai_required_skills", []) or []
        ai_preferred_skills = job.get("ai_preferred_skills", []) or []

        # Legacy fields for backward compatibility
        job_description = (job.get("description", "") or "").lower()
        ai_skills_raw = job.get("ai_skills_required", "") or ""
        if isinstance(ai_skills_raw, list):
            ai_skills_legacy = ai_skills_raw
        else:
            ai_skills_legacy = [ai_skills_raw] if ai_skills_raw else []

        total_score = 0.0

        # Score technical skills matching
        if user_technical_skills:
            tech_score = self._score_technical_skills_match(
                user_technical_skills,
                ai_required_skills,
                ai_preferred_skills,
                ai_skills_legacy,
                job_description,
            )
            total_score += tech_score

        # Score soft skills matching (lower weight)
        if user_soft_skills:
            soft_score = self._score_soft_skills_match(
                user_soft_skills, job_description
            )
            total_score += soft_score

        return min(total_score, 20.0)  # Cap at 20 points

    def _score_technical_skills_match(
        self,
        user_skills: list,
        ai_required: list,
        ai_preferred: list,
        ai_legacy: list,
        job_description: str,
    ) -> float:
        """Score technical skills with required/preferred distinction"""
        if not user_skills:
            return 0.0

        required_matches = 0
        preferred_matches = 0
        legacy_matches = 0
        description_matches = 0

        total_user_skills = len(user_skills)

        for user_skill in user_skills:
            user_skill_lower = user_skill.lower().strip()

            # Check required skills (highest priority)
            if self._skill_matches_list(user_skill_lower, ai_required):
                required_matches += 1
                continue

            # Check preferred skills
            if self._skill_matches_list(user_skill_lower, ai_preferred):
                preferred_matches += 1
                continue

            # Check legacy AI skills
            if self._skill_matches_list(user_skill_lower, ai_legacy):
                legacy_matches += 1
                continue

            # Check job description with synonyms
            if self._skill_matches_description(user_skill_lower, job_description):
                description_matches += 1

        # Calculate weighted score
        score = 0.0

        # Required skills: 3 points each (critical)
        if ai_required:
            required_ratio = required_matches / len(ai_required)
            score += required_ratio * 12.0  # Up to 12 points

        # Preferred skills: 1.5 points each (nice to have)
        if ai_preferred:
            preferred_ratio = preferred_matches / len(ai_preferred)
            score += preferred_ratio * 6.0  # Up to 6 points

        # Legacy and description matches: 1 point each
        if total_user_skills > 0:
            other_ratio = (legacy_matches + description_matches) / total_user_skills
            score += other_ratio * 4.0  # Up to 4 points

        return score

    def _score_soft_skills_match(
        self, user_soft_skills: list, job_description: str
    ) -> float:
        """Score soft skills matching (lower weight than technical)"""
        if not user_soft_skills:
            return 0.0

        soft_skill_keywords = {
            "communication": [
                "communication",
                "communicate",
                "verbal",
                "written",
                "presentation",
            ],
            "leadership": [
                "leadership",
                "lead",
                "manage",
                "mentor",
                "guide",
                "supervise",
            ],
            "teamwork": ["teamwork", "collaboration", "team player", "cooperative"],
            "problem solving": [
                "problem solving",
                "analytical",
                "critical thinking",
                "troubleshoot",
            ],
            "creativity": ["creative", "innovation", "design thinking", "artistic"],
            "adaptability": ["adaptable", "flexible", "agile", "change management"],
            "time management": [
                "time management",
                "organization",
                "prioritization",
                "deadline",
            ],
        }

        matched_soft_skills = 0

        for user_skill in user_soft_skills:
            user_skill_lower = user_skill.lower().strip()

            # Direct match
            if user_skill_lower in job_description:
                matched_soft_skills += 1
                continue

            # Keyword matching
            for skill_category, keywords in soft_skill_keywords.items():
                if user_skill_lower in keywords or any(
                    keyword in user_skill_lower for keyword in keywords
                ):
                    if any(keyword in job_description for keyword in keywords):
                        matched_soft_skills += 1
                        break

        if len(user_soft_skills) > 0:
            soft_ratio = matched_soft_skills / len(user_soft_skills)
            return soft_ratio * 3.0  # Up to 3 points for soft skills

        return 0.0

    def _skill_matches_list(self, user_skill: str, skill_list: list) -> bool:
        """Check if user skill matches any skill in the list with synonyms"""
        if not skill_list:
            return False

        for job_skill in skill_list:
            job_skill_lower = job_skill.lower().strip()

            # Direct match
            if user_skill == job_skill_lower or user_skill in job_skill_lower:
                return True

            # Synonym matching
            if self._are_skills_synonymous(user_skill, job_skill_lower):
                return True

        return False

    def _skill_matches_description(self, user_skill: str, job_description: str) -> bool:
        """Check if user skill matches job description with synonyms"""
        # Direct match
        if user_skill in job_description:
            return True

        # Synonym matching with existing SKILL_SYNONYMS
        for skill_group, synonyms in self.SKILL_SYNONYMS.items():
            if user_skill in synonyms:
                if any(syn in job_description for syn in synonyms):
                    return True

        return False

    def _are_skills_synonymous(self, skill1: str, skill2: str) -> bool:
        """Check if two skills are synonymous"""
        # Enhanced skill synonyms for better matching
        enhanced_synonyms = {
            "javascript": ["js", "javascript", "ecmascript", "node.js", "nodejs"],
            "python": ["python", "py", "python3", "django", "flask"],
            "react": ["react", "reactjs", "react.js", "react native"],
            "angular": ["angular", "angularjs", "angular.js"],
            "vue": ["vue", "vuejs", "vue.js"],
            "css": ["css", "css3", "stylesheets", "styling"],
            "html": ["html", "html5", "markup"],
            "sql": ["sql", "mysql", "postgresql", "database"],
            "aws": ["aws", "amazon web services", "cloud"],
            "docker": ["docker", "containerization", "containers"],
            "kubernetes": ["kubernetes", "k8s", "orchestration"],
            "git": ["git", "version control", "github", "gitlab"],
        }

        # Check if skills are in the same synonym group
        for synonyms in enhanced_synonyms.values():
            if skill1 in synonyms and skill2 in synonyms:
                return True

        # Check existing SKILL_SYNONYMS
        for synonyms in self.SKILL_SYNONYMS.values():
            if skill1 in synonyms and skill2 in synonyms:
                return True

        return False

    def _score_work_arrangement(self, user_prefs: Dict, job: Dict) -> float:
        """
        Enhanced AI-powered work arrangement matching (20 points)

        Prioritizes AI fields over text-based detection:
        - ai_work_arrangement (highest priority)
        - ai_remote_allowed (boolean flag)
        - Legacy text-based detection (fallback)
        """
        user_arrangements = user_prefs.get("work_arrangements", []) or []

        # Handle different data types (list, set, or single string)
        if isinstance(user_arrangements, set):
            user_arrangements = list(user_arrangements)
        elif isinstance(user_arrangements, str):
            # Handle PostgreSQL set format like '{hybrid}' or '{remote,hybrid}'
            if user_arrangements.startswith("{") and user_arrangements.endswith("}"):
                # Remove braces and split by comma
                clean_str = user_arrangements.strip("{}")
                if clean_str:
                    user_arrangements = [item.strip() for item in clean_str.split(",")]
                else:
                    user_arrangements = []
            else:
                user_arrangements = [user_arrangements]
        elif not isinstance(user_arrangements, list):
            user_arrangements = []

        if not user_arrangements:
            return 0.0

        # Get AI-enhanced work arrangement data (highest priority)
        ai_work_arrangement = (job.get("ai_work_arrangement", "") or "").lower()
        ai_remote_allowed = job.get("ai_remote_allowed", False)

        # Legacy fields for backward compatibility (fallback)
        job_title = (job.get("title", "") or "").lower()
        job_description = (job.get("description", "") or "").lower()
        location = (job.get("location", "") or "").lower()
        is_remote = job.get("is_remote", False)

        max_score = 0.0

        # Check if user is flexible/open to any arrangement
        user_is_flexible = any(
            arr.lower() in ["hybrid", "flexible", "any", "open"]
            for arr in user_arrangements
        )

        for arrangement in user_arrangements:
            arrangement_lower = arrangement.lower()

            # FLEXIBLE/HYBRID users are open to ANY work arrangement
            if arrangement_lower in ["hybrid", "flexible", "any", "open"]:
                # Give high score for any job with clear work arrangement
                if ai_work_arrangement:
                    max_score = max(
                        max_score, 18.0
                    )  # High score for any clear arrangement
                elif any([ai_remote_allowed, is_remote]):
                    max_score = max(max_score, 16.0)  # Remote jobs
                else:
                    max_score = max(max_score, 14.0)  # Default on-site assumption

                # Also check specific arrangements for even higher scores
                if "remote" in ai_work_arrangement or ai_remote_allowed:
                    max_score = max(max_score, 20.0)  # Perfect for remote
                elif "hybrid" in ai_work_arrangement:
                    max_score = max(max_score, 20.0)  # Perfect for hybrid
                elif (
                    "on-site" in ai_work_arrangement or "onsite" in ai_work_arrangement
                ):
                    max_score = max(max_score, 20.0)  # Perfect for on-site

            elif arrangement_lower == "remote":
                score = self._score_remote_arrangement(
                    ai_work_arrangement,
                    ai_remote_allowed,
                    is_remote,
                    job_title,
                    job_description,
                    location,
                )
                max_score = max(max_score, score)

            elif arrangement_lower in ["on-site", "onsite", "office"]:
                score = self._score_onsite_arrangement(
                    ai_work_arrangement,
                    ai_remote_allowed,
                    is_remote,
                    job_title,
                    job_description,
                    location,
                )
                max_score = max(max_score, score)

        return max_score

    def _score_remote_arrangement(
        self,
        ai_work_arrangement: str,
        ai_remote_allowed: bool,
        is_remote: bool,
        job_title: str,
        job_description: str,
        location: str,
    ) -> float:
        """Score remote work arrangement matching"""
        # Perfect AI match (20 points)
        if "remote" in ai_work_arrangement:
            return 20.0

        # AI explicitly allows remote (20 points)
        if ai_remote_allowed:
            return 20.0

        # Legacy remote indicators (18 points)
        if is_remote:
            return 18.0

        # Text-based remote indicators (weighted by reliability)
        remote_indicators = {
            "100% remote": 17.0,
            "fully remote": 17.0,
            "work from home": 16.0,
            "remote work": 16.0,
            "remote position": 16.0,
            "remote job": 16.0,
            "work remotely": 15.0,
            "remote": 14.0,
        }

        all_text = f"{job_title} {job_description} {location}"
        for indicator, score in remote_indicators.items():
            if indicator in all_text:
                return score

        return 0.0

    def _score_hybrid_arrangement(
        self,
        ai_work_arrangement: str,
        job_title: str,
        job_description: str,
        location: str,
    ) -> float:
        """Score hybrid work arrangement matching"""
        # Perfect AI match (20 points)
        if "hybrid" in ai_work_arrangement:
            return 20.0

        # Text-based hybrid indicators
        hybrid_indicators = {
            "hybrid work": 18.0,
            "hybrid model": 18.0,
            "hybrid arrangement": 18.0,
            "flexible work": 17.0,
            "work from home some days": 17.0,
            "part remote": 16.0,
            "flexible schedule": 15.0,
            "hybrid": 14.0,
            "flexible": 12.0,
        }

        all_text = f"{job_title} {job_description} {location}"
        for indicator, score in hybrid_indicators.items():
            if indicator in all_text:
                return score

        return 0.0

    def _score_onsite_arrangement(
        self,
        ai_work_arrangement: str,
        ai_remote_allowed: bool,
        is_remote: bool,
        job_title: str,
        job_description: str,
        location: str,
    ) -> float:
        """Score on-site work arrangement matching"""
        # Perfect AI match (20 points)
        if "on-site" in ai_work_arrangement or "onsite" in ai_work_arrangement:
            return 20.0

        # Explicit on-site indicators
        onsite_indicators = [
            "on-site",
            "onsite",
            "office based",
            "in-office",
            "office work",
            "office environment",
            "physical presence required",
        ]

        all_text = f"{job_title} {job_description} {location}"
        for indicator in onsite_indicators:
            if indicator in all_text:
                return 17.0

        # Default assumption: if no remote indicators, likely on-site
        if not (
            ai_remote_allowed
            or is_remote
            or "remote" in all_text
            or "hybrid" in all_text
        ):
            return 14.0  # Moderate score as on-site is often default

        return 0.0

    def _score_salary_match(self, user_prefs: Dict, job: Dict) -> float:
        """
        Enhanced intelligent salary matching with currency conversion (20 points)

        Features:
        - AI-enhanced salary fields prioritized
        - Currency conversion (NGN ↔ USD ↔ EUR ↔ GBP)
        - Range overlap calculation
        - Negotiability flexibility
        - Salary period normalization
        """
        user_currency = user_prefs.get("salary_currency")
        user_min = user_prefs.get("salary_min")
        user_max = user_prefs.get("salary_max")
        salary_negotiable = user_prefs.get("salary_negotiable", True)

        # If user has no salary preferences, return neutral score
        if not any([user_currency, user_min, user_max]):
            return 0.0

        # Get job salary data (prefer AI-enhanced fields)
        job_currency = job.get("ai_salary_currency") or job.get("salary_currency")
        job_min = job.get("ai_salary_min") or job.get("salary_min")
        job_max = job.get("ai_salary_max") or job.get("salary_max")

        # Check if job has any salary data
        job_has_salary = any([job_currency, job_min, job_max])

        # IMPORTANT: If user wants salary info but job has none, give partial points
        # This prevents penalizing the majority of jobs that don't include salary
        if not job_has_salary:
            # Give 10/20 points for jobs without salary data (improved from 8)
            return 10.0

        # Convert to numbers if they're strings
        try:
            if job_min and isinstance(job_min, str):
                job_min = float(job_min.replace(",", ""))
            if job_max and isinstance(job_max, str):
                job_max = float(job_max.replace(",", ""))
            if user_min and isinstance(user_min, str):
                user_min = float(str(user_min).replace(",", ""))
            if user_max and isinstance(user_max, str):
                user_max = float(str(user_max).replace(",", ""))
        except (ValueError, AttributeError):
            pass

        score = 0.0

        # Currency matching with intelligent conversion
        if user_currency and job_currency:
            currency_score = self._score_currency_match(user_currency, job_currency)
            score += currency_score

            # Apply currency conversion if needed
            if currency_score > 0 and currency_score < 4.0:  # Partial currency match
                conversion_factor = self._get_currency_conversion_factor(
                    job_currency, user_currency
                )
                if conversion_factor and job_min:
                    job_min = job_min * conversion_factor
                if conversion_factor and job_max:
                    job_max = job_max * conversion_factor

        # Salary range matching with flexibility
        if user_min or user_max:
            range_score = self._score_salary_range_match(
                user_min, user_max, job_min, job_max, salary_negotiable
            )
            score += range_score

        return min(score, 20.0)  # Cap at 20 points

    def _score_currency_match(self, user_currency: str, job_currency: str) -> float:
        """Score currency matching with intelligent equivalents"""
        if not user_currency or not job_currency:
            return 0.0

        user_curr = user_currency.upper().strip()
        job_curr = job_currency.upper().strip()

        # Perfect match
        if user_curr == job_curr:
            return 4.0

        # Currency equivalents and common variations
        currency_groups = {
            "NGN": ["NGN", "NAIRA", "₦", "NIGERIAN NAIRA"],
            "USD": ["USD", "DOLLAR", "$", "US DOLLAR", "AMERICAN DOLLAR"],
            "EUR": ["EUR", "EURO", "€", "EUROPEAN EURO"],
            "GBP": ["GBP", "POUND", "£", "BRITISH POUND", "STERLING"],
            "CAD": ["CAD", "CANADIAN DOLLAR", "C$"],
            "AUD": ["AUD", "AUSTRALIAN DOLLAR", "A$"],
        }

        user_group = None
        job_group = None

        for currency, variations in currency_groups.items():
            if user_curr in variations:
                user_group = currency
            if job_curr in variations:
                job_group = currency

        if user_group and job_group:
            if user_group == job_group:
                return 4.0

            # Related currencies (easier conversion)
            related_pairs = [
                ("USD", "CAD"),
                ("USD", "AUD"),
                ("GBP", "EUR"),
                ("NGN", "USD"),
                ("NGN", "GBP"),
                ("NGN", "EUR"),
            ]

            for curr1, curr2 in related_pairs:
                if (user_group == curr1 and job_group == curr2) or (
                    user_group == curr2 and job_group == curr1
                ):
                    return 2.0

        return 0.0

    def _get_currency_conversion_factor(
        self, from_currency: str, to_currency: str
    ) -> float:
        """Get approximate currency conversion factor (simplified)"""
        # Simplified conversion rates (should be updated with real-time rates in production)
        conversion_rates = {
            ("USD", "NGN"): 750.0,
            ("EUR", "NGN"): 820.0,
            ("GBP", "NGN"): 950.0,
            ("USD", "EUR"): 0.92,
            ("USD", "GBP"): 0.79,
            ("EUR", "GBP"): 0.86,
        }

        from_curr = from_currency.upper().strip()
        to_curr = to_currency.upper().strip()

        # Direct conversion
        if (from_curr, to_curr) in conversion_rates:
            return conversion_rates[(from_curr, to_curr)]

        # Reverse conversion
        if (to_curr, from_curr) in conversion_rates:
            return 1.0 / conversion_rates[(to_curr, from_curr)]

        return None

    def _score_salary_range_match(
        self,
        user_min: float,
        user_max: float,
        job_min: float,
        job_max: float,
        salary_negotiable: bool,
    ) -> float:
        """Score salary range matching with flexibility"""
        if not any([user_min, user_max, job_min, job_max]):
            return 0.0

        score = 0.0

        # Perfect range overlap
        if user_min and user_max and job_min and job_max:
            if user_min <= job_max and user_max >= job_min:
                overlap_ratio = self._calculate_range_overlap(
                    user_min, user_max, job_min, job_max
                )
                score += overlap_ratio * 6.0  # Up to 6 points for perfect overlap

        # Minimum salary requirements
        if user_min and job_max:
            if job_max >= user_min:
                score += 3.0
            elif salary_negotiable and job_max >= (
                user_min * 0.8
            ):  # 20% flexibility if negotiable
                score += 2.0

        # Maximum budget constraints
        if user_max and job_min:
            if job_min <= user_max:
                score += 2.0
            elif salary_negotiable and job_min <= (
                user_max * 1.2
            ):  # 20% flexibility if negotiable
                score += 1.0

        # Single-sided matches
        if user_min and job_min and not (user_max and job_max):
            if abs(user_min - job_min) / max(user_min, job_min) <= 0.2:  # Within 20%
                score += 2.0

        if user_max and job_max and not (user_min and job_min):
            if abs(user_max - job_max) / max(user_max, job_max) <= 0.2:  # Within 20%
                score += 2.0

        return score

    def _calculate_range_overlap(
        self, user_min: float, user_max: float, job_min: float, job_max: float
    ) -> float:
        """Calculate the overlap ratio between two salary ranges"""
        overlap_start = max(user_min, job_min)
        overlap_end = min(user_max, job_max)

        if overlap_start >= overlap_end:
            return 0.0

        overlap_size = overlap_end - overlap_start
        user_range_size = user_max - user_min
        job_range_size = job_max - job_min

        # Calculate overlap as percentage of the smaller range
        smaller_range = min(user_range_size, job_range_size)
        if smaller_range <= 0:
            return 0.0

        return min(overlap_size / smaller_range, 1.0)

    def _score_contact_availability(self, job: Dict) -> float:
        """Score jobs based on availability of contact information for CTA buttons"""
        score = 0.0

        # Check for job URL (highest priority for apply buttons)
        job_url = job.get("job_url")
        if job_url and job_url.strip():
            score += 6.0  # 6 points for job URL

        # Check for email contact
        email = job.get("email") or job.get("ai_email")
        if email and email.strip():
            score += 3.0  # 3 points for email

        # Check for WhatsApp contact (highest value for user engagement)
        whatsapp = job.get("whatsapp_number") or job.get("ai_whatsapp_number")
        if whatsapp and whatsapp.strip():
            score += 4.0  # 4 points for WhatsApp

        # Bonus for multiple contact methods
        contact_methods = sum(
            [
                1 if job_url and job_url.strip() else 0,
                1 if email and email.strip() else 0,
                1 if whatsapp and whatsapp.strip() else 0,
            ]
        )

        if contact_methods >= 2:
            score += 2.0  # 2 bonus points for multiple contact methods

        return min(score, 10.0)  # Cap at 10 points

    def _score_experience_match(self, user_prefs: Dict, job: Dict) -> float:
        """Enhanced AI-powered experience level matching"""
        user_exp_level = user_prefs.get("experience_level")
        user_years = user_prefs.get("years_of_experience")

        if not user_exp_level and not user_years:
            return 0.0

        # Get AI-enhanced experience data
        ai_job_level = job.get("ai_job_level", []) or []
        ai_years_min = job.get("ai_years_experience_min")
        ai_years_max = job.get("ai_years_experience_max")

        # Legacy fields
        job_description = (job.get("description", "") or "").lower()
        ai_exp_raw = job.get("ai_experience_required", "") or ""
        if isinstance(ai_exp_raw, list):
            ai_exp_required = " ".join(ai_exp_raw).lower() if ai_exp_raw else ""
        else:
            ai_exp_required = ai_exp_raw.lower()

        max_score = 0.0

        # Experience level matching with AI enhancement
        if user_exp_level:
            level_score = self._score_experience_level_match(
                user_exp_level, ai_job_level, job_description, ai_exp_required
            )
            max_score = max(max_score, level_score)

        # Years of experience matching with AI enhancement
        if user_years:
            years_score = self._score_years_experience_match(
                user_years, ai_years_min, ai_years_max, job_description, ai_exp_required
            )
            max_score = max(max_score, years_score)

        return max_score

    def _score_experience_level_match(
        self,
        user_level: str,
        ai_job_level: list,
        job_description: str,
        ai_exp_required: str,
    ) -> float:
        """Score experience level matching with intelligent mapping"""
        if not user_level:
            return 0.0

        user_level_lower = user_level.lower().strip()

        # Experience level hierarchy and mappings
        level_mappings = {
            "entry": [
                "entry",
                "junior",
                "graduate",
                "trainee",
                "intern",
                "beginner",
                "fresh",
            ],
            "junior": ["junior", "entry", "associate", "level 1", "i", "1"],
            "mid": [
                "mid",
                "intermediate",
                "senior",
                "level 2",
                "ii",
                "2",
                "experienced",
            ],
            "senior": ["senior", "lead", "principal", "level 3", "iii", "3", "expert"],
            "lead": ["lead", "senior", "principal", "manager", "head", "chief"],
            "principal": ["principal", "staff", "architect", "expert", "specialist"],
            "executive": ["executive", "director", "vp", "vice president", "c-level"],
        }

        # Find user's level category
        user_category = None
        for category, variations in level_mappings.items():
            if user_level_lower in variations:
                user_category = category
                break

        if not user_category:
            user_category = user_level_lower

        # Check AI job levels first (highest priority)
        if ai_job_level:
            for job_level in ai_job_level:
                job_level_lower = job_level.lower().strip()

                # Direct match
                if user_level_lower == job_level_lower:
                    return 10.0

                # Category match
                job_category = None
                for category, variations in level_mappings.items():
                    if job_level_lower in variations:
                        job_category = category
                        break

                if job_category and user_category:
                    compatibility_score = self._calculate_level_compatibility(
                        user_category, job_category
                    )
                    if compatibility_score > 0:
                        return compatibility_score

        # Fallback to text-based matching
        all_text = f"{job_description} {ai_exp_required}"

        # Direct text matches
        if user_level_lower in all_text:
            return 8.0

        # Category-based text matching
        if user_category in level_mappings:
            for variation in level_mappings[user_category]:
                if variation in all_text:
                    return 6.0

        return 0.0

    def _calculate_level_compatibility(self, user_level: str, job_level: str) -> float:
        """Calculate compatibility score between experience levels"""
        # Experience level progression
        level_hierarchy = [
            "entry",
            "junior",
            "mid",
            "senior",
            "lead",
            "principal",
            "executive",
        ]

        try:
            user_index = level_hierarchy.index(user_level)
            job_index = level_hierarchy.index(job_level)
        except ValueError:
            return 0.0

        # Perfect match
        if user_index == job_index:
            return 10.0

        # Adjacent levels (good compatibility)
        if abs(user_index - job_index) == 1:
            return 8.0

        # Two levels apart (acceptable)
        if abs(user_index - job_index) == 2:
            return 5.0

        # User is overqualified (still acceptable for some roles)
        if user_index > job_index and (user_index - job_index) <= 3:
            return 3.0

        # User is underqualified - be more lenient for entry-level users
        if job_index > user_index:
            gap = job_index - user_index
            if user_index == 0:  # Entry-level user
                if gap == 1:  # Entry -> Junior (very common)
                    return 8.0  # Improved from 2.0
                elif gap == 2:  # Entry -> Mid (still acceptable)
                    return 6.0  # Improved from 2.0
                elif gap == 3:  # Entry -> Senior (stretch but possible)
                    return 4.0  # New - was 0.0
            elif gap <= 2:
                return 3.0  # Slightly improved from 2.0

        return 0.0

    def _score_years_experience_match(
        self,
        user_years: int,
        ai_years_min: int,
        ai_years_max: int,
        job_description: str,
        ai_exp_required: str,
    ) -> float:
        """Score years of experience matching with flexibility"""
        if not user_years:
            return 0.0

        score = 0.0

        # AI-enhanced years matching (highest priority)
        if ai_years_min is not None or ai_years_max is not None:
            if ai_years_min is not None and ai_years_max is not None:
                # Range specified
                if ai_years_min <= user_years <= ai_years_max:
                    return 10.0
                elif user_years >= ai_years_min:
                    # Overqualified but acceptable
                    excess_years = user_years - ai_years_max
                    if excess_years <= 2:
                        return 8.0
                    elif excess_years <= 5:
                        return 6.0
                    else:
                        return 4.0
                elif user_years >= (ai_years_min * 0.8):
                    # Slightly underqualified but close
                    return 5.0
                elif user_years == 0 and ai_years_min <= 3:
                    # Entry-level user applying to 1-3 year jobs (very common)
                    if ai_years_min <= 1:
                        return 8.0  # 0 years vs 1 year - very close
                    elif ai_years_min <= 2:
                        return 6.0  # 0 years vs 2 years - acceptable
                    else:  # ai_years_min == 3
                        return 4.0  # 0 years vs 3 years - stretch but possible
            elif ai_years_min is not None:
                # Only minimum specified
                if user_years >= ai_years_min:
                    return 9.0
                elif user_years >= (ai_years_min * 0.8):
                    return 6.0
            elif ai_years_max is not None:
                # Only maximum specified (rare case)
                if user_years <= ai_years_max:
                    return 8.0

        # Fallback to text-based years extraction
        import re

        all_text = f"{job_description} {ai_exp_required}"

        # Look for year patterns
        year_patterns = re.findall(r"(\d+)\+?\s*(?:years?|yrs?)", all_text)
        if year_patterns:
            required_years = []
            for pattern in year_patterns:
                try:
                    required_years.append(int(pattern))
                except ValueError:
                    continue

            if required_years:
                min_required = min(required_years)
                max_required = max(required_years) if len(required_years) > 1 else None

                if user_years >= min_required:
                    if max_required and user_years <= max_required:
                        return 7.0  # Within range
                    else:
                        return 6.0  # Meets minimum
                elif user_years >= (min_required * 0.8):
                    return 4.0  # Close to minimum

        return score

    def _get_match_reasons(self, user_prefs: Dict, job: Dict) -> List[str]:
        """Get human-readable reasons for the match"""
        reasons = []

        # Job title matches
        user_roles = user_prefs.get("job_roles", [])
        job_title = (job.get("title", "") or "").lower()
        for role in user_roles:
            if role.lower() in job_title:
                reasons.append(f"Job title matches '{role}'")

        # Skills matches
        user_skills = user_prefs.get("technical_skills", []) or []
        job_description = (job.get("description", "") or "").lower()
        for skill in user_skills:
            if skill and skill.lower() in job_description:
                reasons.append(f"Requires '{skill}' skill")

        # Work arrangement matches
        user_arrangements = user_prefs.get("work_arrangements", []) or []
        if "remote" in user_arrangements:
            if job.get("ai_remote_allowed") or "remote" in job_title:
                reasons.append("Remote work available")

        # Location matches - DISABLED
        # user_locations = user_prefs.get("preferred_locations", []) or []
        # job_location = (job.get("location", "") or "").lower()
        # for location in user_locations:
        #     if location.lower() in job_location:
        #         reasons.append(f"Located in {location}")

        return reasons[:3]  # Limit to top 3 reasons

    def format_job_for_whatsapp(self, job: Dict, index: int) -> str:
        """Format job for WhatsApp with intelligent match information"""
        try:
            # Extract key information
            title = job.get("title", "Job Opportunity")
            company = job.get("company", "Company")
            location = job.get("location", "Location not specified")

            # Match information
            match_score = job.get("match_score", 0)
            match_reasons = job.get("match_reasons", [])

            # Build message
            message = f"""*{index}. {title}*
🏢 {company}
📍 {location}"""

            # Add match score and reasons
            if match_score > 0:
                message += f"\n⭐ {match_score:.0f}% match"
                if match_reasons:
                    message += f"\n🎯 {', '.join(match_reasons)}"

            # Add application link
            if job.get("job_url"):
                message += f"\n🔗 Apply: {job['job_url']}"
            elif job.get("ai_application_url"):
                message += f"\n🔗 Apply: {job['ai_application_url']}"

            return message

        except Exception as e:
            logger.error(f"❌ Error formatting job: {e}")
            return f"{index}. Job opportunity available (formatting error)"
