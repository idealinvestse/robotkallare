# GDial - Arkitektur för Kritisk Beredskap och Krishantering

## 🚨 Systemöversikt för Beredskapslägen

**GDial** är designat för kritiska kommunikationsbehov inom svensk regional beredskap:
- **Stab och krisledning** - Snabb aktivering av ledningsgrupper
- **Förstärkning** - Inkallning av specialpersonal och resurser  
- **Katastrofläge** - Massinkallning av beredskapsorganisation
- **Automatisk eskalering** - Obekräftade kontakter till manuell telefonisthantering

## 🎯 Kritiska Krav

### Primära Krav
- ⚡ **Snabbhet**: Nå 100+ personer inom 2 minuter
- 📋 **Kvittenshantering**: Automatisk insamling av bekräftelser
- 🔄 **Eskalering**: Automatisk sortering till manuell hantering
- 🛡️ **Tillförlitlighet**: 99.9% upptid även under kriser
- 📱 **Redundans**: Flera kommunikationskanaler (röst + SMS + interaktiv)
- 🏥 **Prioritering**: Kritiska roller först, sedan stödfunktioner

## 🏗️ Specialiserad Arkitektur

### 1. Databasmodeller för Krishantering

```python
class CrisisLevel(str, Enum):
    STANDBY = "standby"           # Beredskap
    ELEVATED = "elevated"         # Förhöjd beredskap  
    EMERGENCY = "emergency"       # Nödläge
    DISASTER = "disaster"         # Katastrofläge

class PersonnelRole(str, Enum):
    CRISIS_LEADER = "crisis_leader"           # Krisledare
    DEPUTY_LEADER = "deputy_leader"           # Ställföreträdare
    OPERATIONS_CHIEF = "operations_chief"     # Operativ chef
    INFORMATION_OFFICER = "info_officer"      # Informationsansvarig
    LOGISTICS_CHIEF = "logistics_chief"       # Logistikchef
    MEDICAL_OFFICER = "medical_officer"       # Sjukvårdsansvarig
    TECHNICAL_EXPERT = "tech_expert"          # Teknisk expert
    SUPPORT_STAFF = "support_staff"           # Stödpersonal

class CrisisActivation(SQLModel, table=True):
    """Krishantering och beredskapsaktivering"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    crisis_name: str = Field(max_length=200)
    crisis_type: str = Field(max_length=100)  # "översvämning", "brand", "cyberattack"
    crisis_level: CrisisLevel
    geographic_area: str = Field(max_length=200)
    activated_at: datetime = Field(default_factory=datetime.now)
    primary_message: str = Field(max_length=1000)
    urgency_level: int = Field(default=1, ge=1, le=5)
    is_active: bool = True

class PersonnelActivation(SQLModel, table=True):
    """Aktivering av specifik personal"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    crisis_id: uuid.UUID = Field(foreign_key="crisisactivation.id")
    contact_id: uuid.UUID = Field(foreign_key="contact.id")
    assigned_role: PersonnelRole
    priority_level: int = Field(default=3, ge=1, le=5)
    
    # Kommunikationsstatus
    call_attempted_at: Optional[datetime] = None
    call_confirmed: bool = False
    sms_sent_at: Optional[datetime] = None
    sms_confirmed: bool = False
    interactive_response_received: bool = False
    
    # Svar och status
    response_status: str = Field(default="pending")
    response_received_at: Optional[datetime] = None
    
    # Eskalering
    escalated_to_manual: bool = False
    escalated_at: Optional[datetime] = None

class ManualEscalation(SQLModel, table=True):
    """Eskalering till manuell telefonisthantering"""
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    crisis_id: uuid.UUID = Field(foreign_key="crisisactivation.id")
    personnel_activation_id: uuid.UUID = Field(foreign_key="personnelactivation.id")
    escalated_at: datetime = Field(default_factory=datetime.now)
    escalation_reason: str  # "no_answer", "no_confirmation", "technical_failure"
    assigned_to_operator: Optional[str] = None
    contact_successful: bool = False
    contact_result: Optional[str] = None
    resolved_at: Optional[datetime] = None
```

### 2. Kommunikationssekvens

**Automatisk sekvens för varje person:**

1. **🔊 Röstsamtal** (30 sek timeout)
   - Personligt meddelande med krisinfo
   - "Tryck 1 för att bekräfta deltagande"
   - "Tryck 2 för att meddela att du inte kan komma"
   - Om bekräftat → KLART ✅

2. **📱 SMS med kvittens** (5 min timeout)
   - Kort krismeddelande + bekräftelselänk
   - "Svara JA för att bekräfta"
   - Om bekräftat → KLART ✅

3. **🔗 Interaktiv länk** (15 min timeout)
   - Detaljerat meddelande på webbsida
   - Flera svarsalternativ:
     - "✅ Bekräftar - Kan komma omgående"
     - "⏰ Bekräftar - Kommer inom 30 min"
     - "❌ Kan inte komma"
     - "❓ Behöver mer information"
   - Om svar → KLART ✅

4. **👥 Manuell eskalering**
   - Automatisk tilldelning till telefonist
   - Prioritetsordning baserat på roll
   - Telefonist kontaktar manuellt

### 3. Prioriteringsmatris

**Krisnivå → Roller som aktiveras:**

```
STANDBY (Beredskap):
├── Krisledare (Prio 1)
├── Ställföreträdare (Prio 2)
└── Operativ chef (Prio 2)

ELEVATED (Förhöjd):
├── Krisledare (Prio 1)
├── Ställföreträdare (Prio 1)
├── Operativ chef (Prio 2)
├── Informationsansvarig (Prio 2)
└── Logistikchef (Prio 3)

EMERGENCY (Nödläge):
├── Alla ledningsroller (Prio 1-2)
├── Sjukvårdsansvarig (Prio 2)
└── Teknisk expert (Prio 3)

DISASTER (Katastrof):
└── ALLA roller aktiveras (Prio 1-4)
```

### 4. Realtids Dashboard

**Krisdashboard visar:**
- 📊 **Övergripande status**: Bekräftade/Väntande/Eskalerade
- 👥 **Rollfördelning**: Status per personalroll
- ⏱️ **Tidslinje**: Kommunikationsförsök i realtid
- 🚨 **Kritiska luckor**: Obekräftade nyckelroller
- 📞 **Telefonistkö**: Eskalerade ärenden
- 📍 **Geografisk vy**: Regional spridning

**API-endpoints:**
```
POST /api/v1/crisis/activate          # Aktivera krishantering
GET  /api/v1/crisis/{id}/dashboard    # Realtids dashboard
GET  /api/v1/crisis/{id}/personnel    # Personalstatus
POST /api/v1/crisis/{id}/escalate     # Manuell eskalering
PUT  /api/v1/crisis/{id}/resolve      # Avsluta kris
```

### 5. Telefonistgränssnitt

**Eskalering till telefonister:**
- Automatisk fördelning baserat på arbetsbelastning
- Prioritetsordning: Krisledare → Operativ chef → Övriga
- Telefonistverktyg:
  - Kontakthistorik och tidigare svar
  - Fördefinierade skript för olika kristyper
  - Snabbknappar för vanliga svar
  - Automatisk loggning av samtalsresultat

### 6. Säkerhet och Redundans

**Säkerhetsåtgärder:**
- 🔐 **Krypterad kommunikation**: Alla meddelanden krypterade
- 🔑 **Rollbaserad åtkomst**: Endast behöriga kan aktivera kriser
- 📝 **Fullständig loggning**: Alla åtgärder loggas för revision
- 🔄 **Backup-system**: Redundanta kommunikationsvägar
- 📡 **Satellituppkoppling**: För när ordinarie nät fallerar

**Redundans:**
- Primär: Twilio (SMS/Röst)
- Backup: Alternativ SMS-leverantör
- Nöd: Satellittelefon för kritisk personal
- Manuell: Radiokommunikation som sista utväg

## 🚀 Implementering för Beredskap

### Fas 1: Grundläggande Krishantering (2-3 veckor)
1. Databasmodeller för kris och personal
2. Grundläggande kommunikationssekvens
3. Enkel dashboard för krisledning
4. Manuell eskaleringsfunktion

### Fas 2: Automatisering (2 veckor)
1. Automatisk prioritering och rollaktivering
2. Intelligent eskalering till telefonister
3. Realtids dashboard med alla funktioner
4. Interaktiva bekräftelsesidor

### Fas 3: Avancerade Funktioner (2 veckor)
1. Geografisk spridning och zonhantering
2. Mallar för olika kristyper
3. Prestanda-optimering för stora volymer
4. Integration med externa varningssystem

### Fas 4: Säkerhet och Redundans (1 vecka)
1. Säkerhetsförstärkningar
2. Backup-kommunikationsvägar
3. Stresstestning och lastbalansering
4. Dokumentation och utbildning

## 📊 Exempel: Aktivering av Översvämningskris

```json
{
  "crisis_name": "Översvämning Göta Älv",
  "crisis_type": "naturkatastrof_översvämning",
  "crisis_level": "emergency",
  "geographic_area": "Västra Götaland",
  "primary_message": "Kritisk översvämningssituation vid Göta Älv. Omedelbar aktivering av krisledning krävs.",
  "urgency_level": 4,
  "expected_duration": "24 hours",
  "meeting_location": "Regionens kriscentrum, Göteborg"
}
```

**Automatisk aktivering:**
- 🔴 **0-2 min**: Krisledare och ställföreträdare kontaktas (Prio 1)
- 🟡 **2-5 min**: Operativ chef och informationsansvarig (Prio 2)  
- 🟢 **5-10 min**: Logistik och sjukvård (Prio 3)
- 📞 **10+ min**: Obekräftade eskaleras till telefonister

**Förväntad respons:**
- 90% bekräftelse inom 10 minuter
- 95% bekräftelse inom 20 minuter (inkl. manuell hantering)
- Komplett ledningsgrupp aktiverad inom 30 minuter

Denna arkitektur säkerställer snabb, tillförlitlig och spårbar kommunikation för kritiska beredskapslägen med automatisk eskalering för maximal täckning.
