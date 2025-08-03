---
trigger: always_on
---

# GDial - Kodningsriktlinjer för AI Windsurf Agenter

## Översikt

Dessa riktlinjer är specifikt utformade för AI Windsurf kod agenter som arbetar med GDial-projektet. De kombinerar projektets arkitektur med bästa praxis för AI-assisterad utveckling.

## Grundläggande Principer

### 1. Enkelhet Först
- **Föredra enkla lösningar** framför komplexa implementationer
- Undvik över-engineering av funktionalitet
- Implementera den minsta fungerande lösningen först
- Refaktorera endast när komplexiteten motiverar det

### 2. Kodduplicering
- **Kontrollera alltid befintlig kod** innan du implementerar ny funktionalitet
- Sök i repositories, services och utils för liknande implementationer
- Återanvänd befintliga patterns och funktioner
- Skapa gemensamma hjälpfunktioner för återkommande logik

### 3. Miljömedvetenhet
- **Skriv kod som fungerar i alla miljöer**: dev, test, prod
- Använd miljövariabler för konfiguration
- Undvik hårdkodade värden som är miljöspecifika
- Testa att koden fungerar i olika miljöer

## Projektspecifika Riktlinjer

### Backend (Python/FastAPI)

#### Filstruktur och Organisation
```
app/
├── api/           # API endpoints (max 300 rader per fil)
├── models/        # SQLModel datamodeller
├── repositories/  # Dataåtkomst (CRUD-operationer)
├── services/      # Affärslogik (max 250 rader per fil)
├── schemas/       # Pydantic request/response scheman
├── workers/       # Background task workers
├── utils/         # Hjälpfunktioner och utilities
└── realtime/      # WebSocket och realtidsfunktionalitet
```

#### Kodstandarder
- **Filstorlek**: Max 200-300 rader kod per fil
- **Funktioner**: Max 50 rader per funktion
- **Klasser**: Max 200 rader per klass
- **Imports**: Gruppera i ordning: stdlib, third-party, local
- **Typning**: Använd alltid type hints för alla funktioner

#### Databasinteraktion
```python
# RÄTT: Använd repository pattern
class ContactRepository:
    def get_contacts_by_ids(self, session: Session, contact_ids: List[int]) -> List[Contact]:
        return session.exec(select(Contact).where(Contact.id.in_(contact_ids))).all()

# RÄTT: Service layer för affärslogik
class OutreachService:
    def __init__(self, contact_repo: ContactRepository):
        self.contact_repo = contact_repo
    
    def send_to_contacts(self, contact_ids: List[int]) -> None:
        contacts = self.contact_repo.get_contacts_by_ids(session, contact_ids)
        # Affärslogik här
```

#### API Endpoints
```python
# RÄTT: Tydlig endpoint struktur
@router.post("/trigger-sms", response_model=MessageResponse)
async def trigger_sms(
    request: CustomSmsRequest,
    session: Session = Depends(get_session),
    service: OutreachService = Depends(get_outreach_service)
) -> MessageResponse:
    """Send SMS to specified contacts or groups."""
    return await service.send_sms(request)
```

#### Felhantering
```python
# RÄTT: Specifik felhantering
try:
    result = await twilio_client.send_sms(phone, message)
except TwilioException as e:
    logger.error(f"Twilio SMS failed for {phone}: {e}")
    raise HTTPException(status_code=500, detail="SMS sending failed")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Frontend (React/TypeScript)

#### Komponentstruktur
```
src/
├── components/    # Återanvändbara komponenter
├── pages/         # Sidor/vyer (max 200 rader)
├── hooks/         # Custom React hooks
├── services/      # API-tjänster och externa anrop
├── types/         # TypeScript type definitions
└── utils/         # Hjälpfunktioner
```

#### Komponentriktlinjer
```typescript
// RÄTT: Funktionell komponent med TypeScript
interface SmsHistoryTableProps {
  messages: SmsMessage[];
  onRefresh: () => void;
  loading?: boolean;
}

export const SmsHistoryTable: React.FC<SmsHistoryTableProps> = ({
  messages,
  onRefresh,
  loading = false
}) => {
  // Komponentlogik här (max 150 rader)
};
```

#### State Management
```typescript
// RÄTT: Zustand store struktur
interface SmsStore {
  messages: SmsMessage[];
  loading: boolean;
  error: string | null;
  
  // Actions
  fetchMessages: () => Promise<void>;
  sendMessage: (message: CreateSmsRequest) => Promise<void>;
  clearError: () => void;
}

export const useSmsStore = create<SmsStore>((set, get) => ({
  // Implementation
}));
```

#### API Integration
```typescript
// RÄTT: Centraliserad API-tjänst
class SmsService {
  private client = axios.create({
    baseURL: '/api',
    timeout: 10000,
  });

  async sendSms(request: CreateSmsRequest): Promise<SmsResponse> {
    try {
      const response = await this.client.post('/trigger-sms', request);
      return response.data;
    } catch (error) {
      throw new ApiError('Failed to send SMS', error);
    }
  }
}
```

## Testningsriktlinjer

### Backend Testing (pytest)
```python
# RÄTT: Teststruktur med fixtures
@pytest.fixture
def sample_contact():
    return Contact(
        id=1,
        name="Test User",
        phone_numbers=[PhoneNumber(number="+1234567890")]
    )

def test_get_contacts_by_ids(sample_contact):
    # Arrange
    contact_ids = [1, 2, 3]
    
    # Act
    result = contact_repo.get_contacts_by_ids(session, contact_ids)
    
    # Assert
    assert len(result) == 3
    assert result[0].name == "Test User"
```

### Frontend Testing (Vitest)
```typescript
// RÄTT: Komponenttest
describe('SmsHistoryTable', () => {
  it('should display messages correctly', () => {
    const mockMessages = [
      { id: 1, content: 'Test message', status: 'sent' }
    ];
    
    render(<SmsHistoryTable messages={mockMessages} onRefresh={vi.fn()} />);
    
    expect(screen.getByText('Test message')).toBeInTheDocument();
  });
});
```

## Säkerhetsriktlinjer

### Miljövariabler
```python
# RÄTT: Säker konfiguration
class Settings(BaseSettings):
    twilio_account_sid: str
    twilio_auth_token: str = Field(..., min_length=1)
    database_url: str = "sqlite:///./gdial.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

### API-säkerhet
```python
# RÄTT: Validering av Twilio webhooks
def validate_twilio_request(request: Request) -> bool:
    signature = request.headers.get('X-Twilio-Signature', '')
    url = str(request.url)
    body = request.body
    
    return RequestValidator(settings.twilio_auth_token).validate(
        url, body, signature
    )
```

## Prestanda och Skalbarhet

### Databasoptimering
```python
# RÄTT: Effektiva databasfrågor
def get_contacts_with_phone_numbers(session: Session) -> List[Contact]:
    return session.exec(
        select(Contact)
        .options(selectinload(Contact.phone_numbers))
        .where(Contact.active == True)
    ).all()
```

### Asynkron bearbetning
```python
# RÄTT: Background tasks för tunga operationer
@router.post("/trigger-campaign")
async def trigger_campaign(
    request: CampaignRequest,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(process_campaign, request)
    return {"message": "Campaign queued for processing"}
```

## Refaktoreringsriktlinjer

### När ska refaktorering ske?
- **Filstorlek**: När en fil överstiger 300 rader
- **Funktionskomplexitet**: När en funktion överstiger 50 rader
- **Kodduplicering**: När samma logik finns på 3+ ställen
- **Testbarhet**: När kod är svår att testa isolerat

### Refaktoreringsprocess
1. **Identifiera**: Hitta kodområden som behöver förbättras
2. **Testa**: Säkerställ att befintliga tester passerar
3. **Extrahera**: Flytta ut gemensam funktionalitet
4. **Validera**: Kör alla tester efter refaktorering
5. **Dokumentera**: Uppdatera dokumentation vid behov

## Felhantering och Loggning

### Strukturerad loggning
```python
# RÄTT: Strukturerad loggning
logger.info(
    "SMS sent successfully",
    extra={
        "phone_number": phone,
        "message_id": message_id,
        "campaign_id": campaign_id
    }
)
```

### Felhantering patterns
```python
# RÄTT: Graceful degradation
async def send_sms_with_retry(phone: str, message: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await twilio_client.send_sms(phone, message)
        except TwilioException as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

## Dokumentationsriktlinjer

### Koddokumentation
```python
# RÄTT: Tydlig docstring
def send_scheduled_messages(session: Session, scheduled_time: datetime) -> int:
    """
    Send all messages scheduled for the specified time.
    
    Args:
        session: Database session
        scheduled_time: Time to check for scheduled messages
        
    Returns:
        Number of messages sent successfully
        
    Raises:
        TwilioException: If SMS sending fails
        DatabaseError: If database operations fail
    """
```

### API-dokumentation
```python
# RÄTT: FastAPI dokumentation
@router.post(
    "/trigger-sms",
    summary="Send SMS to contacts",
    description="Send SMS messages to specified contacts or groups",
    response_model=MessageResponse,
    responses={
        400: {"description": "Invalid request data"},
        500: {"description": "SMS sending failed"}
    }
)
```

## Deployment och CI/CD

### Docker-riktlinjer
```dockerfile
# RÄTT: Multi-stage build
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Miljöhantering
- **Utveckling**: Använd `.env` för lokala inställningar
- **Test**: Separata testdatabaser och mock-tjänster
- **Produktion**: Miljövariabler via container orchestration

## Sammanfattning för AI Agenter

### Innan du börjar koda:
1. **Undersök befintlig kod** för liknande funktionalitet
2. **Kontrollera projektstruktur** och följ etablerade patterns
3. **Identifiera rätt lager** (repository, service, API) för din kod
4. **Planera tester** för ny funktionalitet

### Under utveckling:
1. **Håll filer små** (200-300 rader)
2. **Skriv tydliga funktioner** (max 50 rader)
3. **Använd typning** konsekvent
4. **Hantera fel** gracefully
5. **Logga viktiga händelser** strukturerat

### Efter implementering:
1. **Skriv tester** för ny funktionalitet
2. **Uppdatera dokumentation** vid behov
3. **Kontrollera prestanda** för kritiska paths
4. **Validera säkerhet** för externa integrationer

### Kom ihåg:
- **Enkelhet över komplexitet**
- **Återanvändning över duplicering**
- **Testbarhet över snabba lösningar**
- **Säkerhet över bekvämlighet**
- **Dokumentation över antaganden**
