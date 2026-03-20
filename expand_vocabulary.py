#!/usr/bin/env python3
"""Expand vocabulary with domain-specific skills that were missing."""

import pandas as pd
from src.config.settings import SKILLS_VOCAB_PATH

# Load existing vocabulary
df = pd.read_csv(SKILLS_VOCAB_PATH)
existing_skills = set(df['skill'].str.lower().str.strip())

# Comprehensive domain-specific skills to add
new_skills_to_add = [
    # ─── MECHANICAL ENGINEERING ───
    'structural analysis', 'stress analysis', 'thermodynamics', 'fluid mechanics',
    'manufacturing engineering', 'cnc', 'molding', 'sheet metal design', 
    'materials science', 'metallurgy', 'vibration analysis', 'modal analysis',
    'fea (finite element analysis)', 'fem', 'cfm', 'computational fluid dynamics',
    'mechanical design', 'piping design', 'pressure vessel design', 'pump selection',
    '3d modeling', 'technical drawing', 'dimensioning', 'gear design',
    'bearing design', 'tolerance analysis', 'quality assurance in manufacturing',
    'lean manufacturing', 'six sigma', 'process improvement', 'value engineering',
    'product engineering', 'design for manufacturing', 'design for assembly',
    'failure mode analysis', 'root cause analysis', 'reliability engineering',
    'prototyping', 'testing and validation', 'performance testing',
    
    # ─── CIVIL ENGINEERING ───
    'structural engineering', 'civil structures', 'building construction',
    'reinforced concrete', 'rcc', 'steel structures', 'precast concrete',
    'building codes', 'construction management', 'project management',
    'site supervision', 'material testing', 'concrete technology',
    'geotechnical engineering', 'foundation design', 'soil mechanics',
    'groundwater assessment', 'slope stability', 'retaining wall design',
    'environmental engineering', 'water treatment', 'wastewater treatment',
    'transportation engineering', 'road design', 'highway engineering',
    'pavement design', 'traffic engineering', 'railway engineering',
    'surveying', 'gps surveying', 'total station', 'leveling',
    'cost estimation', 'project cost control', 'value for money',
    'tender preparation', 'contract management', 'legal documentation',
    'quality control', 'quality assurance', 'inspection',
    'bim (building information modeling)', '3d cad modeling', 'revit',
    'architectural design', 'interior design', 'urban planning',
    'environmental impact assessment', 'sustainability',
    
    # ─── ELECTRICAL ENGINEERING ───
    'power systems', 'power generation', 'power transmission', 'power distribution',
    'electrical machines', 'transformer design', 'motor design', 'generator design',
    'high voltage engineering', 'protection systems', 'relay coordination',
    'load flow analysis', 'short circuit analysis', 'stability analysis',
    'switchgear', 'circuit breakers', 'distribution equipment',
    'control systems', 'automation', 'plc (programmable logic controller)',
    'scada (supervisory control and data acquisition)', 'iot', 'embedded systems',
    'circuit design', 'pcb design', 'pcb layout', 'signal integrity',
    'vlsi', 'fpga', 'asic', 'digital design', 'analog design',
    'power electronics', 'converter design', 'inverter design', 'power supply',
    'microcontrollers', 'dsp', 'real-time systems', 'firmware development',
    'communication systems', 'telecommunications', 'signal processing',
    'wireless communication', 'antenna design', 'rf design',
    'electromagnetics', 'electromagnetic compatibility', 'shielding',
    'testing and measurement', 'oscilloscope', 'multimeter', 'power analyzer',
    'standards and compliance', 'iec standards', 'ieee standards',
    
    # ─── AEROSPACE ENGINEERING ───
    'aerodynamics', 'flight mechanics', 'aircraft design', 'spacecraft design',
    'propulsion systems', 'jet engine design', 'rocket engine design',
    'structural analysis for aircraft', 'fatigue analysis', 'fracture mechanics',
    'avionics', 'navigation systems', 'autopilot', 'flight control systems',
    'aircraft maintenance', 'engine maintenance', 'structural maintenance',
    'aircraft systems', 'hydraulic systems', 'pneumatic systems', 'electrical systems',
    'composite materials', 'aluminum alloys', 'titanium alloys',
    'aircraft manufacturing', 'assembly processes', 'quality control in aviation',
    'air traffic management', 'airport operations', 'airline management',
    # UAV/Drone specific
    'drone design', 'uav design', 'quadrotor', 'flight control',
    'computer vision', 'autonomous systems', 'path planning',
    
    # ─── CHEMICAL ENGINEERING ───
    'chemical processes', 'process design', 'reactor design', 'heat transfer',
    'mass transfer', 'thermodynamics', 'fluid mechanics', 'corrosion',
    'material selection', 'scaling up', 'pilot plant', 'commercial plant',
    'distillation', 'separation processes', 'filtration', 'crystallization',
    'pharmaceutical engineering', 'drug manufacturing', 'gmp (good manufacturing practice)',
    'food engineering', 'food processing', 'food safety', 'quality assurance',
    'environmental remediation', 'water purification', 'air pollution control',
    'hazardous waste management', 'process safety', 'psm (process safety management)',
    'hazop analysis', 'risk assessment', 'safety systems',
    'plant automation', 'scada systems', 'process control',
    'chemical analysis', 'spectroscopy', 'chromatography',
    'troubleshooting', 'optimization', 'process improvement',
    
    # ─── BIOMEDICAL ENGINEERING ───
    'medical device design', 'biocompatibility', 'tissue engineering',
    'biomechanics', 'orthopedic engineering', 'cardiac engineering',
    'clinical engineering', 'hospital equipment', 'medical system maintenance',
    'biomedical signals', 'eeg', 'ecg', 'signal acquisition',
    'medical imaging', 'mri', 'ct scan', 'ultrasound',
    'image processing', 'computer visualization', '3d reconstruction',
    'bioinformatics', 'genomics', 'proteomics', 'molecular biology',
    'pharmaceutical sciences', 'drug formulation', 'toxicology',
    'regulatory compliance', 'fda approval', 'medical standards',
    'clinical trials', 'patient monitoring', 'telemedicine',
    
    # ─── FINANCE & ACCOUNTING ───
    'accounting', 'bookkeeping', 'general ledger', 'accounts payable',
    'accounts receivable', 'journal entries', 'trial balance', 'balance sheet',
    'income statement', 'cash flow statement', 'financial reporting',
    'audit', 'internal audit', 'external audit', 'compliance audit',
    'financial analysis', 'ratio analysis', 'trend analysis', 'variance analysis',
    'budgeting', 'forecasting', 'variance analysis', 'cost control',
    'cost accounting', 'cost allocation', 'overhead allocation',
    'tax accounting', 'income tax', 'sales tax', 'gst', 'vat',
    'financial modeling', 'valuation', 'dcf analysis', 'sensitivity analysis',
    'investment analysis', 'portfolio management', 'risk management',
    'derivatives', 'options', 'futures', 'swaps',
    'banking', 'lending', 'credit analysis', 'risk assessment',
    'commercial banking', 'investment banking', 'corporate finance',
    'mergers and acquisitions', 'financial due diligence',
    'treasury management', 'working capital management',
    'financial planning', 'retirement planning', 'estate planning',
    'insurance', 'underwriting', 'claims management',
    'sap', 'oracle financials', 'quickbooks', 'xero', 'tally',
    'ms excel', 'pivot tables', 'vba', 'financial modeling in excel',
    'gst India', 'tds', 'gratuity', 'provident fund', 'esop',
    
    # ─── HUMAN RESOURCES ───
    'recruiting', 'talent acquisition', 'recruitment marketing',
    'job posting', 'resume screening', 'candidate sourcing',
    'behavioral interviewing', 'competency assessment', 'psychometric testing',
    'onboarding', 'employee orientation', 'induction training',
    'performance management', 'performance appraisal', 'performance planning',
    'goal setting', 'okr (objectives and key results)', 'kpia',
    'compensation', 'salary planning', 'benefits administration',
    'payroll', 'payroll processing', 'statutory compliance',
    'provident fund', 'gratuity', 'esop', 'stock options',
    'employee relations', 'conflict resolution', 'grievance handling',
    'labor law', 'employment law', 'compliance', 'workplace policies',
    'training and development', 'l&d', 'corporate training',
    'coaching', 'mentoring', 'succession planning',
    'organizational development', 'change management', 'culture building',
    'employee engagement', 'survey analysis', 'feedback management',
    'worklife balance', 'wellness programs', 'employee assistance',
    'business partnering', 'strategic hr', 'hr analytics',
    'hr systems', 'hris', 'erp', 'workday', 'sap hr',
    'employee data management', 'reporting', 'dashboards',
    'diversity and inclusion', 'equity', 'belonging',
    
    # ─── MARKETING ───
    'content marketing', 'blogging', 'copywriting', 'content strategy',
    'seo (search engine optimization)', 'sem (search engine marketing)',
    'ppc (pay-per-click)', 'google ads', 'facebook ads', 'social media advertising',
    'social media marketing', 'facebook', 'instagram', 'twitter', 'linkedin', 'youtube',
    'community management', 'brand management', 'brand strategy',
    'digital marketing', 'web analytics', 'google analytics',
    'marketing automation', 'crm', 'customer relationship management',
    'email marketing', 'marketing automation platforms', 'hubspot',
    'market research', 'consumer research', 'competitive analysis',
    'product positioning', 'market segmentation', 'target audience',
    'pricing strategy', 'value proposition', 'customer journey',
    'conversion rate optimization', 'a/b testing', 'user experience testing',
    'marketing metrics', 'kpi', 'roi', 'customer acquisition cost',
    'customer lifetime value', 'retention marketing', 'customer loyalty',
    'influencer marketing', 'viral marketing', 'event marketing',
    'pr (public relations)', 'media relations', 'press release',
    'crisis management', 'reputation management',
    'offline marketing', 'print advertising', 'tv advertising', 'radio',
    'direct mail', 'outdoor advertising', 'guerrilla marketing',
    'partnership marketing', 'affiliate marketing', 'referral marketing',
    'video marketing', 'interactive media', 'augmented reality',
    
    # ─── OPERATIONS MANAGEMENT ───
    'supply chain management', 'procurement', 'vendor management',
    'logistics', 'warehouse management', 'inventory management',
    'planning', 'forecasting', 'demand planning', 'production planning',
    'scheduling', 'resource allocation', 'capacity planning',
    'quality management', 'quality control', 'quality assurance',
    'lean management', 'six sigma', 'kaizen', 'continuous improvement',
    'process optimization', 'business process improvement', 'process modeling',
    'operational excellence', 'efficiency', 'cost reduction',
    'risk management', 'business continuity', 'disaster recovery',
    'vendor scorecards', 'kpi tracking', 'performance monitoring',
    'operational reporting', 'analytics', 'process analytics',
    'inventory modeling', 'abc analysis', 'safety stock', 'eoq',
    'just-in-time', 'kanban', 'lean six sigma',
    
    # ─── SALES ───
    'sales management', 'sales strategy', 'sales planning', 'territory management',
    'account management', 'key account management', 'client relationship',
    'pipeline management', 'deal closure', 'negotiation', 'contract negotiation',
    'customer acquisition', 'customer retention', 'customer service',
    'sales forecasting', 'sales projection', 'revenue forecasting',
    'market intelligence', 'competitive intelligence', 'market trends',
    'sales enablement', 'sales training', 'sales coaching',
    'crm', 'salesforce', 'sales tool', 'sales process',
    'presentation skills', 'communication', 'listening skills',
    'product knowledge', 'technical product knowledge',
    'pricing', 'discount strategy', 'margin management',
    'lead generation', 'lead qualification', 'sales funnel',
    'cold calling', 'prospecting', 'networking',
    'inside sales', 'field sales', 'remote sales',
    
    # ─── PRODUCT MANAGEMENT ───
    'product strategy', 'product roadmap', 'product planning',
    'product requirements', 'prd', 'user stories', 'use cases',
    'product design', 'ux', 'ui', 'user research', 'user testing',
    'market analysis', 'competitive analysis', 'market sizing',
    'product positioning', 'go-to-market strategy', 'launch planning',
    'agile', 'scrum', 'kanban', 'sprint planning', 'backlog management',
    'metrics and analytics', 'product metrics', 'user engagement metrics',
    'a/b testing', 'experimentation', 'data-driven decision making',
    'stakeholder management', 'cross-functional collaboration',
    'product prioritization', 'feature prioritization', 'roadmap evolution',
    'customer feedback', 'product feedback', 'user interviews',
    'product vision', 'strategy communication', 'product evangelism',
    
    # ─── PROJECT MANAGEMENT ───
    'project planning', 'project scope', 'work breakdown structure',
    'schedule management', 'timeline', 'critical path', 'gantt charts',
    'resource planning', 'resource allocation', 'team composition',
    'budget management', 'cost estimation', 'cost control', 'cost tracking',
    'risk management', 'risk assessment', 'mitigation strategies',
    'quality planning', 'quality assurance', 'quality control',
    'stakeholder management', 'communication planning', 'reporting',
    'procurement', 'vendor selection', 'contract management',
    'change management', 'scope management', 'baseline management',
    'earned value management', 'performance tracking', 'metrics',
    'issue resolution', 'issue tracking', 'decision making',
    'meeting management', 'documentation', 'project artifacts',
    'agile methodologies', 'scrum', 'kanban', 'xp', 'lean',
    'waterfall', 'iterative development', 'incremental delivery',
    'ms project', 'jira', 'asana', 'monday.com', 'trello',
    'team leadership', 'conflict resolution', 'motivation',
    
    # ─── DESIGN (GENERAL) ───
    'graphic design', 'visual design', 'branding', 'logo design',
    'typography', 'color theory', 'layout design', 'composition',
    'photography', 'image editing', 'digital manipulation',
    'print design', 'packaging design', 'label design',
    'web design', 'ui design', 'ux design', 'interaction design',
    'wireframing', 'prototyping', 'user testing', 'user research',
    'design thinking', 'design systems', 'design guidelines',
    'responsive design', 'mobile design', 'accessibility',
    'animation', 'motion design', 'video production',
    'adobe creative suite', 'photoshop', 'illustrator', 'indesign',
    'figma', 'sketch', 'xd', 'prototyping tools',
    'design tools', '3d design', 'cad', 'blender', 'unity',
    
    # ─── ADDITIONAL BUSINESS SKILLS ───
    'business analysis', 'requirements analysis', 'user requirements',
    'business process improvement', 'process mapping', 'flowcharting',
    'stakeholder analysis', 'impact analysis', 'feasibility analysis',
    'risk assessment', 'swot analysis', 'gap analysis',
    'business intelligence', 'bi', 'analytics', 'data analytics',
    'business metrics', 'kpi', 'dashboard', 'reporting',
    'documentation', 'technical writing', 'user documentation',
    'strategic planning', 'business strategy', 'vision setting',
    'leadership', 'team management', 'people management',
    'communication', 'presentation', 'public speaking',
    'negotiation', 'persuasion', 'interpersonal skills',
    'decision making', 'critical thinking', 'problem solving',
    'creativity', 'innovation', 'brainstorming',
    'change management', 'organizational change', 'transformation',
    'training delivery', 'training design', 'instructional design',
    'coaching and mentoring', 'performance management',
]

# Normalize new skills (lowercase, strip)
new_skills_normalized = {s.lower().strip() for s in new_skills_to_add}

# Find what's truly new
newly_added = new_skills_normalized - existing_skills

print(f"Current vocabulary size: {len(existing_skills)}")
print(f"New skills to add: {len(newly_added)}")
print(f"Total after merge: {len(existing_skills) + len(newly_added)}")

# Create updated dataframe
all_skills = sorted(list(existing_skills | new_skills_normalized))
updated_df = pd.DataFrame({'skill': all_skills})

# Save updated vocabulary
updated_df.to_csv(SKILLS_VOCAB_PATH, index=False)
print(f"\n✓ Updated vocabulary saved to {SKILLS_VOCAB_PATH}")
print(f"  - Original: {len(existing_skills)} skills")
print(f"  - Added: {len(newly_added)} new skills")
print(f"  - Final: {len(updated_df)} skills")

# Show sample of new skills added
print(f"\nSample of newly added skills:")
for skill in sorted(list(newly_added))[:30]:
    print(f"  + {skill}")
print(f"  ... and {len(newly_added) - 30} more")
