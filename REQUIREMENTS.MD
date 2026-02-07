# REQUIREMENTS.MD

## Project Overview
A voice-first, offline-capable mobile application that helps Indian citizens discover and apply for government welfare schemes through intelligent eligibility assessment, strategic application planning, and community-validated guidance.

---

## 1. FUNCTIONAL REQUIREMENTS

### 1.1 Layer 1: Guided Eligibility Interview Engine

**Core Capability**: Natural language understanding of user life situations, not static forms.

#### Interview Flow
- **Natural Language Input**: User describes situation in conversational Hindi/Hinglish
  - Example: "Mera husband 5 saal pehle pass ho gaya, mere paas 2 bacche hain, aur main part-time tailoring ka kaam karti hoon"
  - System extracts: marital status (widow), time since event (5 years), dependents (2 children), income source (part-time tailoring)

- **Contextual Understanding**: System identifies key eligibility factors
  - Age bracket
  - Dependent count and ages
  - Income level and sources
  - Geographic location (state/district)
  - Disability status
  - Caste/category
  - Property ownership

- **Intelligent Follow-up Questions**: Branching logic based on context
  - If age > 60 → Ask about pension eligibility, health conditions
  - If disabled → Ask about disability certificate, percentage
  - If income < threshold → Ask about BPL card status, ration card type
  - If widow with children → Ask about children's ages, education status
  - If farmer → Ask about land ownership, crop type, irrigation access

#### Eligibility Discovery
- **Comprehensive Scheme Matching**: Discover ALL eligible schemes, not just obvious ones
  - Cross-reference user profile against 1000+ scheme eligibility rules
  - Identify schemes across multiple ministries/departments
  - Surface lesser-known schemes with high approval rates

- **Transparent Reasoning**: Explain match/non-match for each scheme
  - Example: "✓ You're eligible for Widow Pension because you're under 60 with dependent children"
  - Example: "✗ You're NOT eligible for Senior Citizen Allowance until you turn 60 (2 years from now)"
  - Example: "? You MIGHT be eligible for Disability Pension if you have 40%+ disability certificate"

#### Output Format
- **Ranked Eligibility List**:
  - Scheme name (Hindi + English)
  - Confidence score (e.g., 94% confident)
  - Eligibility explanation (why you qualify)
  - Benefit amount (monthly/lumpsum)
  - Required documents
  - Estimated processing time
  - Success rate in your district

---

### 1.2 Layer 2: Scheme Optimizer (Strategy Engine)

**Core Capability**: Strategic application planning, not just a list of schemes.

#### Comparison Matrix
Display eligible schemes in structured comparison:
- Benefit amount (monthly recurring vs. one-time lumpsum)
- Processing time (weeks to approval)
- Required documents (count + complexity)
- Approval rate in user's district
- Mutual exclusivity rules (which schemes conflict)
- Co-eligibility opportunities (which schemes stack)

#### Constraint Detection
- **Mutual Exclusivity**: Flag schemes that cannot be claimed together
  - Example: "You cannot receive both Old Age Pension and Widow Pension simultaneously"
  
- **Sequential Dependencies**: Identify schemes requiring prior approvals
  - Example: "BPL card approval increases chances for housing scheme by 40%"
  
- **Seasonal Windows**: Alert time-sensitive applications
  - Example: "Scholarship applications close on March 31st—apply within 8 weeks"

#### Optimal Application Strategy Generation

**Strategy Components**:

1. **Sequencing Logic**:
   - Which scheme to apply FIRST? (Fastest approval = credibility builder)
   - Which schemes can run in PARALLEL? (No document conflicts)
   - Which scheme to apply LAST? (Builds on approval momentum)

2. **Timeline Visualization**:
   ```
   Weeks 1-8:   Scheme A (Widow Pension) - Fast approval, builds credibility
   Weeks 4-12:  Scheme B (Child Education Grant) - Parallel, no conflicts
   Weeks 12+:   Scheme C (Housing Subsidy) - Requires Scheme A approval
   ```

3. **Total Benefit Calculation**:
   - Monthly recurring: ₹1,500/month (Scheme A + B)
   - Annual lumpsum: ₹25,000 (Scheme C)
   - Total first-year benefit: ₹43,000

4. **Document Consolidation**:
   - Consolidated list of ALL required documents across schemes
   - Highlight reusable documents (Aadhaar needed for 3 schemes)
   - Flag missing documents (need to obtain disability certificate)
   - **On-Device OCR Verifier** (Document Gap Filler):
     - Uses Google ML Kit (offline OCR)
     - User scans Aadhaar/Ration card with phone camera
     - System auto-extracts: Name, age, address, Aadhaar number, ration card type
     - Auto-verifies eligibility points without manual data entry
     - Reduces data entry errors (common rejection reason)
     - Works offline (no document upload to cloud)
     - Privacy-preserving: OCR happens on-device, extracted data encrypted locally

#### Trade-off Explanations
System must explain strategic reasoning:
- "Scheme X gives ₹500/month but approves in 8 weeks (recommended first for momentum)"
- "Scheme Y gives ₹800/month but takes 16 weeks and requires 8 documents"
- "Applying for Scheme X first increases your Scheme Y approval chances by 35%"

#### Actionable Output
- **Step-by-step Action Plan**: Printable/shareable document
  - Week-by-week tasks
  - Document checklist
  - Application submission addresses
  - Follow-up schedule
  - Escalation contacts if delayed

---

### 1.3 Layer 3: Community Validation Network

**Core Capability**: Peer-verified success stories, not theoretical eligibility.

#### Success Story Matching
- **Personalized Matches**: Show 2-3 success stories from user's district
  - Same age bracket (±5 years)
  - Similar life event (widow, disabled, farmer, etc.)
  - Comparable income level
  - Same geographic region

- **Story Details**:
  - Anonymized name + photo (if consent given): "Sunita D., Age 42, Pune District"
  - Actual timeline: "Applied Jan 2024, approved March 2024 (9 weeks)"
  - Blockers faced: "Had to resubmit income certificate twice"
  - Tips learned: "Visit office on Tuesday mornings—less crowded"
  - Final outcome: "Approved for ₹600/month widow pension"

#### District Statistics
- **Aggregate Success Metrics**:
  - "91% of widows in Maharashtra who applied for widow pension were approved within 12 weeks"
  - "78% had to resubmit documents at least once (most common: income certificate)"
  - "15% needed additional income verification from Tehsildar"
  - "Average benefit amount: ₹650/month"

#### Anonymized Peer Chat
- **Direct Peer Communication**:
  - User can ask clarifying questions to successful applicants
  - Example: "Which office did you visit for income certificate?"
  - Peer responds within 48 hours (incentivized via community points)
  - All PII stripped from chat (no phone numbers, addresses shared)

#### Trust Signals
- **Verification Badges**:
  - ✓ Verified by NGO partner (XYZ Foundation)
  - ✓ Cross-checked with government records
  - ✓ Peer responded within 48 hours (active community member)
  - ✓ Story updated within last 6 months (not stale)

#### Network Effect
- **Self-Reinforcing Growth**:
  - Every successful application adds to the pool
  - Users incentivized to share success stories (community karma points)
  - More stories = better matching = higher trust = more users

---

### 1.4 Voice Interface

**Primary Interaction Mode**: Voice-first design for low-literacy users.

#### Voice Input
- **Language Support**: Hindi + Hinglish with natural code-mixing
  - Example: "Mera husband pass hai ki nahi, aur mere paas 2 bacche hain"
  - System handles: "Mujhe widow pension chahiye" or "I want widow pension"

- **Voice Capture**:
  - Large microphone icon (easy tap target for elderly)
  - Haptic feedback (phone vibration) confirms voice capture
  - Real-time transcription (user sees text appearing as they speak)
  - Edit capability (user can correct transcription errors via text)

#### Voice Output
- **Text-to-Speech**: Conversational Hindi (not robotic)
  - Natural intonation and pacing
  - Adjustable speech rate (slower for elderly)
  - Repeat option (user can replay last response)

#### Fallback Text Input
- **Accessibility Alternatives**:
  - Text input for deaf users
  - Text input for noisy environments
  - Keyboard shortcuts for power users
  - Copy-paste support for sharing information

---

### 1.5 Offline-First Core Functionality

**Design Principle**: All core features work without internet.

#### Downloaded Data Package
Must fit on 4GB Android phone:
- All schemes for user's state (eligibility rules, benefits, documents)
- 5,000+ district success stories + statistics
- Offline LLM model (smaller variant for interview logic)
- UI assets (images, icons, fonts)
- Total size: <200MB

#### Offline Features
- **Full Eligibility Interview**: Complete branching interview engine works offline
- **Scheme Comparison**: All comparison and optimization logic offline
- **Success Story Browsing**: Read peer stories without internet
- **Note-taking**: Save strategy, document checklist, application notes locally
- **Voice Transcription**: On-device speech-to-text (no cloud dependency)

#### Sync on Internet Return
- **Background Sync**:
  - User's anonymized query results sent to cloud (improves model)
  - New success stories downloaded
  - Scheme rule updates pulled
  - User can trigger manual sync anytime

#### Data Persistence
- **No Data Loss**: All offline work persists even if internet never returns
- Local SQLite database for user data
- Encrypted local storage for sensitive information
- Export capability (user can backup data to SD card)

---

### 1.7 Pro Mode (Agent-in-the-Loop for Village Volunteers)

**Core Capability**: Bulk application management for village volunteers, NGO workers, and ethical agents serving elderly/illiterate neighbors.

#### Target Users
- **Village Volunteers**: Gram Panchayat members, ASHA workers, Anganwadi workers
- **NGO Field Workers**: Social workers helping multiple beneficiaries
- **Ethical Agents**: Agents who want to serve more clients faster (with transparency)
- **Family Members**: Adult children helping elderly parents

#### Pro Mode Features

**Bulk Interview Management**:
- Manage 10-50 beneficiaries from single device
- Each beneficiary has separate profile (privacy-preserved)
- Quick-switch between profiles (no re-login)
- Bulk document scanning (scan 10 Aadhaar cards in sequence)

**Offline-First Bulk Operations**:
- Conduct interviews offline (village with no connectivity)
- All data stored locally, encrypted per beneficiary
- Sync when internet available (bulk upload)
- No data loss if internet never returns

**Application Tracking Dashboard**:
- See all beneficiaries' application status in one view
- Filter by: pending, applied, approved, rejected
- Alerts for deadlines (scholarship closing in 2 weeks)
- Bulk reminders (5 beneficiaries need to submit income cert)

**Transparency & Accountability**:
- Beneficiary can see their own data anytime (QR code access)
- Agent cannot modify beneficiary data without consent
- All actions logged (audit trail for NGO oversight)
- Beneficiary receives SMS when agent submits application on their behalf

**Incentive Model**:
- Agents earn ₹50-100 per successful application (paid by NGO/government, not beneficiary)
- Gamification: Leaderboard for most beneficiaries helped
- Certification: "Verified Nyaaya.ai Agent" badge after training

**Training & Support**:
- In-app training videos (Hindi, 5-10 min each)
- Practice mode (mock interviews with fake data)
- Helpline for agents (WhatsApp support group)
- Monthly webinars (Q&A with government officers)

#### Why Pro Mode is Critical

**Problem**: 40% of target users are elderly (65+) or illiterate. They cannot use the app independently.

**Solution**: Empower trusted intermediaries (family, volunteers, ethical agents) to help at scale.

**Why Not Just Let Agents Use Regular Mode?**
- Regular mode: 1 user per device (agent would need 50 phones)
- No bulk operations (agent wastes time repeating same steps)
- No accountability (agent could exploit beneficiaries)

**Pro Mode Benefits**:
- **Scale**: 1 agent helps 50 beneficiaries (vs 5 without app)
- **Speed**: Bulk operations save 80% time per beneficiary
- **Trust**: Transparency prevents exploitation
- **Offline**: Works in villages with no connectivity

#### Pro Mode Constraints

**Privacy Safeguards**:
- Agent sees only data beneficiary consents to share
- Beneficiary can revoke agent access anytime (via SMS code)
- Agent cannot transfer beneficiary data to another agent
- All PII encrypted with beneficiary-specific key (agent cannot decrypt)

**Abuse Prevention**:
- Agent must be verified by NGO partner (background check)
- Agent activity monitored (flag suspicious patterns)
- Beneficiary can report abuse (in-app button + helpline)
- Agent suspended if 3+ abuse reports

**Offline Sync Limits**:
- Max 50 beneficiaries per agent device (prevents data hoarding)
- Sync required every 30 days (prevents stale data)
- Beneficiary data auto-deleted from agent device after application submitted

---

### 1.8 Government Data Integration & Validation

**Data Source**: Official government portals, not guesses.

#### Eligibility Rules Sourcing
- **Official Sources**:
  - Ministry of Social Justice schemes
  - Ministry of Rural Development schemes
  - State government welfare portals
  - District administration circulars

- **Version Control**:
  - Each rule tagged with: "Last updated: 15-Jan-2025"
  - Source attribution: "Source: Ministry of Social Justice Notification #123/2024"
  - Change log: "Modified in Nov 2024: Income threshold increased from ₹10,000 to ₹12,000"

#### Quarterly Rule Updates
- **Update Cycle**:
  - Quarterly review of all scheme rules
  - Push updates to all users via app
  - Notify users if their eligibility changed due to rule updates

#### Outdated Scheme Flagging
- **Staleness Detection**:
  - System flags schemes not updated in 6+ months
  - Warning: "Note: This scheme was modified in Nov 2024. Your eligibility may have changed. Verify with local office."

#### Hallucination Prevention
- **Validation Layer**:
  - All LLM eligibility outputs validated against hardcoded rules
  - If LLM output conflicts with rules, rules win
  - Confidence score reduced if LLM reasoning unclear
  - Human-in-the-loop review for edge cases (flagged for NGO partner review)

---

## 2. NON-FUNCTIONAL REQUIREMENTS

### 2.1 Performance

#### Latency Targets
- **Voice Response**: <2 seconds on 2G networks
  - Critical: Users drop off if response feels slow
  - Optimize: On-device inference, aggressive caching

- **Scheme Search/Match**: <500ms
  - User expects instant results after interview
  - Pre-compute eligibility scores where possible

- **Peer Story Retrieval**: <1 second
  - Must feel real-time, not backend processing
  - Local indexing of downloaded stories

- **Voice Transcription**: Real-time streaming
  - User sees text appearing as they speak
  - <100ms latency per word

- **Model Inference**: <1 second per interview question
  - Otherwise users lose focus and drop off
  - Use quantized models for speed

---

### 2.2 Accessibility & Device Support

#### Minimum Device Specifications
- **Target Device**: ₹5,000 Android phone
  - Android 8.0 or higher
  - 4GB RAM
  - 2G network support
  - No GPS required
  - No NFC required
  - Basic camera (for document scanning)

#### App Size & Data Usage
- **App Size**: <200MB (including offline data)
  - Must fit on phones with limited storage
  - Incremental updates (delta patches, not full downloads)

- **Data Usage**: <50MB/month for sync
  - Minimize bandwidth for rural users
  - Compress all network transfers
  - Allow user to control sync frequency

#### Accessibility Features
- **Vision Impaired**:
  - Adjustable font size (150%, 200%, 300%)
  - High contrast mode
  - Screen reader support (TalkBack compatible)
  - Audio descriptions for all UI elements

- **Motor Impaired**:
  - Large tap targets (minimum 48x48dp)
  - Voice-only navigation option
  - No time-sensitive interactions

- **Hearing Impaired**:
  - Text fallback for all voice interactions
  - Visual feedback for all audio cues
  - Closed captions for video content (future)

#### Battery & Performance
- **Dark Mode**: Built-in (reduces battery drain on OLED screens)
- **Low Power Mode**: Reduces animations, background sync
- **Efficient Rendering**: Minimize CPU/GPU usage

---

### 2.3 Privacy & Security

#### Zero PII Storage Without Consent
- **Opt-in Model**: User explicitly consents to data collection
- **Granular Permissions**: Separate consent for:
  - Eligibility interview data
  - Peer network participation
  - Research/product improvement
  - Location data (district-level only)

#### Encryption
- **At Rest**: AES-256 encryption for local database
- **In Transit**: TLS 1.3 for all network communication
- **Key Management**: User-specific encryption keys (not shared across devices)

#### Anonymization
- **PII Stripping Before Community Layer**:
  - Name → Age band (35-40 years)
  - Exact location → District only
  - Income → Income band (₹10,000-₹15,000)
  - Phone number → Never stored
  - Aadhaar → Never stored

#### Consent Model
- **User Controls**:
  - Opt-in to peer network (can disable anytime)
  - Separate consent for data used in research
  - Consent withdrawal deletes all associated data within 30 days

#### Data Deletion
- **Right to be Forgotten**: User can request full deletion within 30 days
- **DPDP Act Compliance**: Align with India's Digital Personal Data Protection Act
- **Audit Trail**: Encrypted log of deletion requests

#### Audit Trail
- **Access Logging**: Encrypted log of who accessed what data
- **Compliance Verification**: Auditable by regulators
- **Retention**: Logs retained for 2 years, then deleted

#### No Third-Party Tracking
- **Zero Surveillance**:
  - No Google Analytics
  - No ad networks
  - No data brokers
  - No social media pixels
  - No cross-app tracking

#### Government Data Ethics
- **Official APIs Only**: No scraping of non-public data
- **Respect Robots.txt**: Honor government website policies
- **Attribution**: Cite all government sources

---

### 2.4 Reliability & Trust

#### Uptime SLA
- **Community Validation Layer**: 99.5% uptime
  - Trust is fragile; downtime damages credibility
  - Redundant servers across regions
  - Automated failover

#### Data Freshness
- **Scheme Database**: Zero stale data
  - Update within 24 hours of government rule change
  - Automated monitoring of government portals
  - Manual verification by NGO partners

#### Peer Story Accuracy
- **Verification Process**:
  - All stories verified by NGO partners before publishing
  - Cross-check against government records where possible
  - Flag suspicious stories for manual review
  - Remove fake/spam stories within 24 hours

#### User Data Backup
- **Backup Schedule**: Daily incremental backups
- **Recovery Time**: Recoverable within 24 hours
- **Redundancy**: Multi-region backup storage

---

### 2.5 Scalability

#### Concurrent Users
- **Target**: 10,000+ concurrent users per district
- **Architecture**: Horizontally scalable stateless API
- **Load Balancing**: Auto-scaling based on traffic

#### Scheme Database
- **Coverage**: 1,000+ schemes across 28 states
- **Storage**: Manageable on device (<50MB compressed)
- **Indexing**: Fast lookup via local SQLite FTS

#### Peer Network
- **Scale**: 100,000+ verified success stories
- **Distributed Indexing**: Stories indexed by district/scheme/age
- **Efficient Matching**: Pre-computed similarity scores

#### Backend Architecture
- **Stateless API**: No session affinity required
- **Microservices**: Independent scaling of components
- **CDN**: Static assets served via CDN
- **Database**: Sharded by state/district

---

### 2.6 Localization & Multilingual Support

#### Primary Language
- **Hindi + Hinglish**: Natural code-mixing as users speak
  - Not translated English (bad UX)
  - Natively conversational Hindi
  - Handle regional dialects

#### Future Languages
- **Regional Expansion**:
  - Tamil (Tamil Nadu)
  - Telugu (Andhra Pradesh, Telangana)
  - Kannada (Karnataka)
  - Bengali (West Bengal)
  - Marathi (Maharashtra)

#### Scheme Names
- **Multilingual Display**:
  - Local language + Hindi + English
  - Example: "વિધવા પેન્શન / विधवा पेंशन / Widow Pension"

---

## 3. CONSTRAINTS & ASSUMPTIONS

### 3.1 Government Data Unavailability

**Assumption**: Official APIs are incomplete, outdated, or non-existent.

**Mitigations**:
- **Community Validation as Ground Truth**: If many users report discrepancies, system alerts and updates
  - Example: "10 users reported Scheme X requires Document Y, but official portal says no doc needed"
  
- **NGO Partnerships**: Partner with NGOs who manually verify scheme rules
  - NGOs have on-ground presence and government contacts
  - NGOs can escalate data quality issues to government

- **Crowdsourced Updates**: Users can flag outdated information
  - Flagged content reviewed by NGO partners within 48 hours

---

### 3.2 LLM Hallucination on Eligibility

**Risk**: LLM tells user they're eligible when they're not → user wastes time/money applying.

**Mitigations**:
- **Hardcoded Rule Validation**: All LLM outputs validated against hardcoded rules before showing user
  - If LLM says eligible but rules say not, rules win
  
- **Confidence Scores**: System says "I'm 94% confident" not "You're definitely eligible"
  - Lower confidence triggers manual review flag
  
- **Multi-turn Clarification**: User can ask follow-up questions in interview
  - Not one-shot prediction; iterative refinement
  
- **Explainable AI**: System shows reasoning for each eligibility decision
  - User can spot errors in reasoning

---

### 3.3 User Data Quality

**Assumption**: Users may lie, be confused, or misunderstand their situation.

**Mitigations**:
- **Verification Prompts**: System asks for clarification
  - "You said income is ₹15,000/month. Is this household income or personal income?"
  - "Do you have a recent pay slip or bank statement to verify?"
  
- **Consequence Explanation**: System explains risks of inaccurate data
  - "If income is actually higher, your application will be rejected later. Better to be accurate now."
  
- **Sanity Checks**: System flags implausible data
  - Example: "You said you're 35 years old but have a 20-year-old child. Please verify."

---

### 3.4 Low Digital Literacy

**Assumption**: Users can't read fine print or understand technical language.

**Mitigations**:
- **Simple Language**: All text at 6th-grade reading level max
  - No jargon, no bureaucratic language
  - Short sentences, active voice
  
- **Visual Communication**: Icons + voice for all key concepts
  - ✓ Eligible = green checkmark + "Aap eligible hain"
  - ✗ Not eligible = red X + "Aap eligible nahi hain"
  
- **Relatable Examples**: Use neighbor/peer examples
  - "Like your neighbor Ravi—he got this scheme because he's over 60 and has BPL card"

---

### 3.5 Regulatory Uncertainty (DPDP Act)

**Assumption**: Data privacy regulations in India are evolving; enforcement unclear.

**Mitigations**:
- **Privacy by Default**: Collect minimum data, anonymize early, encrypt always
  - Don't collect data "just in case"
  
- **Transparency**: Be upfront with users
  - "We anonymize your data so your identity is protected in our peer network"
  
- **Consent Management**: Granular, revocable consent
  - User can withdraw consent anytime
  
- **Legal Review**: Quarterly legal review of privacy practices

---

### 3.6 Internet Connectivity

**Assumption**: Users in rural areas have 2G or spotty WiFi.

**Mitigations**:
- **Offline-First Design**: All core features work without internet
  - Interview, comparison, peer stories all offline
  
- **On-Demand Sync**: User triggers sync when they have internet
  - Don't force background sync (wastes data)
  
- **Graceful Degradation**: App never crashes due to network issues
  - Show cached data with "Last updated: 2 days ago" timestamp

---

### 3.7 Fraud / Agent Interference

**Risk**: Unscrupulous agents sabotage the app to protect their ₹300-500 commission.

**Mitigations**:
- **Offline Availability**: App available free via offline download
  - Can't block offline mode
  - Peer-to-peer sharing via Bluetooth/SD card
  
- **Community Trust**: Peer stories more credible than agent promises
  - Real people, real outcomes, verifiable
  
- **Agent Partnership Model**: Convert agents into allies
  - Agents can use app to serve more clients faster
  - Agents earn commission for verified successful applications

---

### 3.8 Scheme Rule Changes

**Assumption**: Government schemes change quarterly (eligibility, benefit amounts, required docs).

**Mitigations**:
- **Quarterly Update Cycle**: Push new rules via app every 3 months
  - Automated monitoring of government portals
  
- **Version Control**: Show user which rules changed
  - "Income threshold increased from ₹10,000 to ₹12,000 in Nov 2024"
  
- **Grandfathering**: User's eligibility determined by rules at time of application
  - If rules change after user applies, old rules still apply to their case

---

## 4. SUCCESS METRICS

### 4.1 User Adoption Metrics

#### Active Users
- **Target**: 50,000 active users per district within 6 months (pilot state)
- **Measurement**: Monthly active users (MAU)
- **Segmentation**: By age, gender, scheme type

#### Interview Completion Rate
- **Target**: >85% of users finish eligibility interview without dropout
- **Measurement**: % of users who complete interview vs. start
- **Dropout Analysis**: Identify where users drop off (which question)

#### Peer Story Trust Rating
- **Target**: Average 4.5/5 stars, users find peer stories "very helpful"
- **Measurement**: User rating after reading peer story
- **Qualitative Feedback**: "What did you find most helpful?"

---

### 4.2 Impact Metrics

#### Schemes Discovered Per User
- **Target**: Average 3-5 schemes per user (up from 0-1 if using portal)
- **Measurement**: # of eligible schemes shown per user
- **Comparison**: Benchmark against government portal usage

#### Application Success Rate
- **Target**: 85%+ of users who apply get at least one scheme approved
- **Measurement**: Track user-reported outcomes
- **Verification**: Cross-check with government records where possible

#### Total Benefits Claimed
- **Target**: ₹500M in benefits claimed over 12 months (pilot state)
- **Measurement**: Sum of all approved benefit amounts
- **Attribution**: User reports "I applied because of this app"

#### Time Saved Per User
- **Target**: 10 hours saved per user vs. hiring agent
- **Measurement**: User survey: "How much time did this app save you?"
- **Comparison**: Benchmark against agent-assisted applications

#### The Dignity Score (Human Impact Metric)
- **Definition**: Reduction in physical hardship and indignity faced by rural users
- **Components**:
  - **Office Visits Avoided**: Average 3-5 visits to government offices (each visit = 4-6 hours travel + waiting)
  - **Travel Costs Saved**: ₹200-500 per visit (bus fare, food, lost wages)
  - **Rejection Cycles Reduced**: 78% of users face rejection due to incomplete docs. App reduces this to <20% (pre-verification via OCR)
  - **Agent Dependency Eliminated**: Users no longer need to pay ₹300-500 to agents or face exploitation
  - **Autonomy Restored**: Users understand their own eligibility (not dependent on agent's word)
- **Target**: 
  - Reduce office visits from 4 to 1 (75% reduction)
  - Save ₹1,500 per user in travel + agent fees
  - 80% of users report "I felt respected and understood" (dignity preserved)
- **Measurement**: 
  - User survey: "How many times did you visit the office?" (before vs after app)
  - "Did you feel the app treated you with respect?" (5-point scale)
  - "Would you recommend this to your neighbor?" (Net Promoter Score)
- **Why This Matters**: 
  - Government schemes are a RIGHT, not charity. Users shouldn't face indignity to access their benefits.
  - Rural users (especially women, elderly, disabled) face harassment, long waits, and dismissive treatment at offices.
  - App empowers users with knowledge → they can advocate for themselves → dignity preserved.

---

### 4.3 Community Network Metrics

#### Success Story Engagement
- **Target**: >60% of users read at least 1 peer story
- **Measurement**: % of users who view peer story page
- **Depth**: Average # of stories read per user

#### Peer Chat Activation
- **Target**: >40% of users ask questions to peers
- **Measurement**: % of users who send at least 1 peer chat message
- **Response Rate**: % of peer chats answered within 48 hours

#### Network Effect
- **Target**: Doubling of network size every 6 months
- **Measurement**: # of verified success stories added per month
- **Virality**: # of new users referred by existing users

---

### 4.4 Technical Metrics

#### Eligibility Accuracy
- **Target**: >95% accuracy (system-recommended schemes match ground truth)
- **Measurement**: Audit sample of 1,000 users, verify eligibility manually
- **Error Analysis**: Categorize false positives vs. false negatives

#### Offline Functionality Uptime
- **Target**: 99.9% of offline features work reliably
- **Measurement**: Crash-free sessions, error logs
- **Device Coverage**: Test on 50+ device models

#### Interview Comprehension
- **Target**: >80% of users report "I finally understand why I was rejected"
- **Measurement**: User survey after interview
- **Qualitative**: "Did the app explain eligibility clearly?"

---

## 5. OUT OF SCOPE (MVP)

### Not Included in Initial Release

#### Real-time Government Application Submission
- **Reason**: Government APIs not available; integration too complex
- **Workaround**: Users still file manually or via agent, but with clarity from app
- **Future**: Add when government APIs become available

#### Video Call with Government Officers
- **Reason**: Too complex for MVP; requires government partnership
- **Workaround**: App provides phone numbers and office hours
- **Future**: Add if user demand is high

#### Integration with ALL State Schemes
- **Reason**: 28 states = too much data for MVP
- **Workaround**: Start with 2-3 pilot states (Maharashtra, Rajasthan, Uttar Pradesh)
- **Future**: Expand state-by-state based on demand

#### Multi-language Support Beyond Hindi
- **Reason**: Focus on Hindi belt for MVP
- **Workaround**: Hindi + Hinglish covers 40%+ of target users
- **Future**: Add Tamil, Telugu, Kannada, Bengali based on demand

#### Biometric Authentication
- **Reason**: Overkill for MVP; adds complexity
- **Workaround**: Simple OTP-based authentication
- **Future**: Add if security concerns arise

#### Government API Integration
- **Reason**: APIs incomplete/unavailable
- **Workaround**: Use manually curated data + community validation
- **Future**: Integrate APIs as they become available

#### Document Upload & OCR
- **Reason**: Complex; requires backend storage
- **Workaround**: App provides document checklist; user manages docs
- **Future**: Add OCR for automatic document verification

#### In-app Payment for Agent Services
- **Reason**: Payment gateway integration complex
- **Workaround**: Users pay agents directly if they choose to hire
- **Future**: Add if agent partnership model scales

---

## 6. TECHNICAL ARCHITECTURE (High-Level)

### 6.1 Mobile App (Android)
- **Framework**: React Native or Flutter (cross-platform future)
- **Local Database**: SQLite with FTS5 (full-text search)
- **Offline LLM**: Quantized model (GGUF format, <500MB)
- **Voice**: On-device speech-to-text (Vosk or similar)
- **Encryption**: SQLCipher for database encryption

### 6.2 Backend API
- **Framework**: Node.js/Express or Python/FastAPI
- **Database**: PostgreSQL (scheme rules, user data)
- **Search**: Elasticsearch (peer story search)
- **Cache**: Redis (frequently accessed data)
- **Storage**: S3-compatible (peer story images)

### 6.3 Data Pipeline
- **Scheme Scraping**: Automated scraping of government portals
- **Rule Extraction**: LLM-based extraction + manual verification
- **Version Control**: Git-based versioning of scheme rules
- **Update Distribution**: Delta updates pushed to app

### 6.4 Community Platform
- **Peer Matching**: Vector similarity search (embeddings)
- **Anonymization**: PII stripping pipeline
- **Verification**: NGO partner dashboard for story verification
- **Moderation**: Automated + manual content moderation

---

## 7. DEPENDENCIES & RISKS

### 7.1 External Dependencies
- **Government Data**: Dependent on government portal availability
- **NGO Partnerships**: Dependent on NGO capacity for verification
- **Device Compatibility**: Dependent on Android ecosystem
- **Network Infrastructure**: Dependent on 2G/3G coverage

### 7.2 Key Risks
- **Regulatory Risk**: DPDP Act enforcement could require architecture changes
- **Data Quality Risk**: Government data may be inaccurate/outdated
- **Adoption Risk**: Users may not trust app without agent endorsement
- **Scalability Risk**: Viral growth could overwhelm backend
- **Security Risk**: Data breach could destroy trust

### 7.3 Mitigation Strategies
- **Regulatory**: Privacy-by-default design, legal review
- **Data Quality**: Community validation, NGO partnerships
- **Adoption**: Pilot with trusted NGOs, word-of-mouth growth
- **Scalability**: Cloud auto-scaling, CDN, caching
- **Security**: Encryption, penetration testing, bug bounty

---

## 8. DEVELOPMENT PHASES

### Phase 1: MVP (Months 1-6)
- Eligibility interview engine (Hindi only)
- Scheme comparison & optimizer
- Offline functionality
- 2-3 pilot states (Maharashtra, Rajasthan, UP)
- 1,000 verified peer stories
- Android app only

### Phase 2: Scale (Months 7-12)
- Community validation network (peer chat)
- 5 additional states
- 10,000+ peer stories
- Performance optimization
- Security audit

### Phase 3: Expand (Months 13-18)
- Multi-language support (Tamil, Telugu, Kannada)
- All 28 states
- Government API integration (if available)
- Agent partnership program
- iOS app

---

## APPENDIX

### A. Glossary
- **BPL**: Below Poverty Line (income threshold for welfare schemes)
- **Tehsildar**: Sub-district administrative officer
- **Aadhaar**: 12-digit unique identity number for Indian residents
- **DPDP Act**: Digital Personal Data Protection Act (India's privacy law)
- **NGO**: Non-Governmental Organization
- **PII**: Personally Identifiable Information
- **TTS**: Text-to-Speech
- **FTS**: Full-Text Search
- **LLM**: Large Language Model

### B. References
- Ministry of Social Justice: https://socialjustice.gov.in/
- Ministry of Rural Development: https://rural.nic.in/
- DPDP Act: https://www.meity.gov.in/dpdpa-2023
- Aadhaar: https://uidai.gov.in/

---

**Document Version**: 1.0  
**Last Updated**: February 7, 2026  
**Owner**: Product Team  
**Status**: Draft for Review
