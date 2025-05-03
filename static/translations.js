/**
 * Nödlarmsystem Översättningsfil
 * Denna fil innehåller huvudöversättningsfunktionalitet.
 * Språkfiler laddas som translations_sv.js och translations_en.js
 */

// Importera svenska översättningar om de inte finns
if (typeof translations_sv === 'undefined') {
  document.write('<script src="/ringbot/static/translations_sv.js"></script>');
}

// För bakåtkompatibilitet
const translations = {
  // Header och titel
  "pageTitle": "Nödlarmsystem Dashboard",
  "headerTitle": "Nödlarmsystem",
  "systemReady": "System redo",
  
  // Nödkontrollpanel
  "emergencyControlTitle": "Nödlarmskontroll",
  "systemStatus": "Systemstatus",
  "refreshStats": "Uppdatera statistik",
  "startEmergencyCalls": "Starta nödsamtal",
  "defaultEmergencyMessage": "Standard nödmeddelande",
  "allContacts": "Alla kontakter",
  
  // Statistiketiketter
  "totalCalls": "Totalt antal samtal",
  "completed": "Genomförda",
  "noAnswer": "Inget svar",
  "manualHandling": "Manuell hantering",
  "errors": "Fel",
  "lastCall": "Senaste samtal",
  
  // Flikar
  "messages": "Meddelanden",
  "callLogs": "Samtalslogg",
  "contacts": "Kontakter",
  "groups": "Grupper",
  "systemLog": "Systemlogg",
  "Response Settings": "Kvitteringsinställningar",
  
  // Meddelanden-flik
  "emergencyMessages": "Nödmeddelanden",
  "refresh": "Uppdatera",
  "createNewMessage": "Skapa nytt meddelande",
  
  // Loggflik
  "callActivityLog": "Samtalsaktivitetslogg",
  "refreshLogs": "Uppdatera logg", 
  "allTime": "All tid",
  "today": "Idag",
  "last7Days": "Senaste 7 dagarna",
  "last30Days": "Senaste 30 dagarna",
  "time": "Tid",
  "contact": "Kontakt",
  "phone": "Telefon",
  "message": "Meddelande",
  "status": "Status",
  "response": "Svar",
  "previous": "Föregående", 
  "next": "Nästa", 
  "page": "Sida",
  
  // Kontakter-flik
  "emergencyContacts": "Nödkontakter",
  "addNewContact": "Lägg till ny kontakt",
  "name": "Namn",
  "email": "E-post",
  "phoneNumbers": "Telefonnummer",
  "actions": "Åtgärder",
  
  // Grupper-flik
  "contactGroups": "Kontaktgrupper",
  "addNewGroup": "Lägg till ny grupp",
  
  // Knappar och åtgärder
  "edit": "Redigera",
  "delete": "Ta bort",
  "view": "Visa",
  "callGroup": "Ring grupp",
  "cancel": "Avbryt",
  "save": "Spara",
  "saveChanges": "Spara ändringar",
  "close": "Stäng",
  "saveMessage": "Spara meddelande",
  "saveContact": "Spara kontakt",
  "saveGroup": "Spara grupp",
  
  // Formuläretiketter
  "messageNameTitle": "Meddelandenamn/titel*",
  "saveAsTemplate": "Spara som återanvändbar mall",
  "messageContent": "Meddelandeinnehåll*",
  "messagePreview": "Förhandsvisning:",
  "yourMessageWillAppear": "Ditt meddelande kommer att visas här när du skriver...",
  "messageHelpText": "Detta meddelande kommer att läsas upp för kontakter. Var tydlig, koncis och ge specifika instruktioner.",
  "notes": "Anteckningar",
  "addPhoneNumber": "Lägg till telefonnummer",
  "description": "Beskrivning",
  "addContactsToGroup": "Lägg till kontakter i grupp",
  "groupMembers": "Gruppmedlemmar",
  
  // Modaltitlar
  "createNewEmergencyMessage": "Skapa nytt nödmeddelande",
  "editEmergencyMessage": "Redigera nödmeddelande",
  "addNewContactTitle": "Lägg till ny kontakt",
  "editContactTitle": "Redigera kontakt",
  "addNewGroupTitle": "Lägg till ny grupp",
  "editGroupTitle": "Redigera grupp",
  "groupDetailsTitle": "Gruppdetaljer",
  
  // Bekräftelsemeddelanden
  "confirmDelete": "Är du säker på att du vill ta bort ",
  "confirmDeleteMessage": "Är du säker på att du vill ta bort meddelandet",
  "confirmDeleteContact": "Är du säker på att du vill ta bort",
  "confirmDeleteGroup": "Är du säker på att du vill ta bort gruppen",
  "confirmCallGroup": "Är du säker på att du vill ringa alla kontakter i gruppen",
  "confirmTriggerDialer": "Är du säker på att du vill utlösa nödlarmet?",
  "confirmTriggerDialerGroup": "Detta kommer att ringa alla kontakter i gruppen",
  "confirmTriggerDialerAll": "Detta kommer att ringa ALLA kontakter i systemet.",
  "confirmTriggerDialerMessage": "Använder meddelande:",
  "thisActionCannotBeUndone": "Denna åtgärd kan inte ångras.",
  
  // Statusindikatorer
  "statusCompleted": "genomförd",
  "statusNoAnswer": "inget svar",
  "statusManual": "manuell",
  "statusError": "fel",
  "noResponse": "Inget svar",
  "default": "Standard",
  "template": "Mall",
  "oneTime": "Engång",
  "noMembers": "Inga medlemmar i denna grupp",
  "membersCount": "medlemmar",
  "unknown": "Okänd",
  "never": "Aldrig",
  "acknowledged": "Bekräftad",
  "needAssistance": "Behöver hjälp",
  "emergency": "Nödläge",
  "noMessagesFound": "Inga meddelanden hittades. Skapa ett nytt nödmeddelande för att komma igång.",
  "noGroupsFound": "Inga grupper hittades. Skapa en ny grupp för att komma igång.",
  "noGroupsAvailable": "Inga grupper tillgängliga",
  "noContactsAvailable": "Inga kontakter tillgängliga",
  "noDescription": "Ingen beskrivning",
  "noMembersInGroup": "Inga medlemmar i denna grupp",
  "members": "Medlemmar",
  "contacts": "Kontakter",
  "noResponseSettingsFound": "Inga svarsinställningar hittades.",
  "updated": "Uppdaterad",
  "useThisMessage": "Använd detta meddelande",
  "systemError": "Systemfel",
  
  // DTMF Response Settings
  "Button": "Knapp",
  "Description": "Beskrivning",
  "Response Message": "Svarsmeddelande",
  "Edit Response Message": "Redigera svarsmeddelande",
  "A short description of what this button does.": "En kort beskrivning av vad denna knapp gör.",
  "This message will be read to the contact when they press this button during a call.": "Detta meddelande kommer att läsas upp för kontakten när de trycker på denna knapp under ett samtal.",
  
  // Settings UI
  "settings": "Inställningar",
  "generalSettings": "Allmänna inställningar",
  "dtmfSettings": "DTMF-inställningar",
  "smsSettings": "SMS-inställningar", 
  "notificationSettings": "Aviseringsinställningar",
  "systemSettingsInfo": "Dessa inställningar styr systembeteendet och kan påverka alla delar av GDial.",
  "dtmfSettingsInfo": "Dessa inställningar styr hur DTMF-svar hanteras i nödsamtal.",
  "smsSettingsInfo": "Dessa inställningar styr hur SMS-meddelanden formateras och skickas.",
  "notificationSettingsInfo": "Dessa inställningar styr hur och när systemaviseringar skickas till administratörer.",
  "setting": "Inställning",
  "value": "Värde",
  "maxAttempts": "Max antal försök",
  "maxAttemptsHelp": "Maximalt antal försök för DTMF-inmatning innan samtalet avslutas.",
  "inputTimeout": "Inmatningstimeout (sek)",
  "inputTimeoutHelp": "Antal sekunder att vänta på DTMF-inmatning innan samtalet avslutas.",
  "confirmResponse": "Bekräfta svar",
  "confirmResponseHelp": "Begär bekräftelse på DTMF-svar ('Du tryckte på X. Är detta korrekt?').",
  "retryOnInvalid": "Försök igen vid ogiltigt",
  "retryOnInvalidHelp": "Tillåt ny inmatning om ogiltig siffra trycks in.",
  "additionalDigits": "Ytterligare siffror",
  "additionalDigitsHelp": "Ytterligare siffror som accepteras utöver de grundläggande 1,2,3.",
  "universalGather": "Universell insamling",
  "universalGatherHelp": "Lägg till insamlingsfunktionalitet till alla utgående meddelanden.",
  "includeSenderName": "Inkludera avsändarnamn",
  "includeSenderNameHelp": "Lägg till systemets namn i början av SMS-meddelanden.",
  "messagePrefix": "Meddelandeprefix",
  "messagePrefixHelp": "Text som läggs till i början av varje SMS-meddelande.",
  "messageSuffix": "Meddelandesuffix",
  "messageSuffixHelp": "Text som läggs till i slutet av varje SMS-meddelande.",
  "maxLength": "Maxlängd",
  "maxLengthHelp": "Maximal längd för SMS-meddelanden (standard är 160 tecken).",
  "splitLongMessages": "Dela långa meddelanden",
  "splitLongMessagesHelp": "Dela automatiskt meddelanden som överskrider maxlängden.",
  "batchDelayMs": "Batchfördröjning (ms)",
  "batchDelayMsHelp": "Fördröjning mellan att skicka grupper av SMS-meddelanden.",
  "batchSize": "Batchstorlek",
  "batchSizeHelp": "Antal meddelanden per batch.",
  "statusCallbackUrl": "Status-callback URL",
  "statusCallbackUrlHelp": "URL för att ta emot callbacks om leveransstatus för SMS.",
  "adminEmail": "Admin-e-post",
  "adminEmailHelp": "E-postadress för systemadministratören.",
  "notifyOnEmergency": "Avisera vid nödläge",
  "notifyOnEmergencyHelp": "Skicka avisering till administratören när nödsamtal startas.",
  "notifyOnError": "Avisera vid fel",
  "notifyOnErrorHelp": "Skicka avisering till administratören vid systemfel.",
  "failureThresholdPct": "Feltröskel (%)",
  "failureThresholdPctHelp": "Skicka avisering när samtal/SMS misslyckas över denna procentnivå.",
  "dailyReports": "Dagliga rapporter",
  "dailyReportsHelp": "Skicka dagliga statusrapporter till administratören.",
  "weeklyReports": "Veckovisa rapporter",
  "weeklyReportsHelp": "Skicka veckovisa sammanfattningsrapporter till administratören."
};

// Håll reda på aktuellt språk, default är svenska
let currentLanguage = 'sv';

// Funktion för att hämta översättning
function __(key, defaultText = null) {
  // Välj rätt översättningsobjekt baserat på aktuellt språk
  const translationObj = currentLanguage === 'sv' ? translations_sv : translations_en;
  
  if (translationObj && translationObj[key] !== undefined) {
    return translationObj[key];
  }
  // Fallback till gamla translations objekt
  if (translations[key] !== undefined) {
    return translations[key];
  }
  return defaultText || key;
}

// Funktion för att byta språk
function changeLanguage(lang) {
  if (lang === 'sv' || lang === 'en') {
    currentLanguage = lang;
    document.documentElement.lang = lang;
    // Spara språkval i localStorage
    localStorage.setItem('gdial_language', lang);
    // Återapplicera alla översättningar
    if (typeof applyTranslations === 'function') {
      applyTranslations();
    } else {
      applyBasicTranslations();
    }
  }
}

// Grundläggande funktion för att uppdatera UI-element med översättningar
function applyBasicTranslations() {
  // Översätt titlar och statiska element
  if (document.getElementById('page-title')) 
    document.getElementById('page-title').textContent = __('pageTitle');
  
  if (document.getElementById('header-title'))
    document.getElementById('header-title').textContent = __('headerTitle'); 
  
  if (document.getElementById('system-status'))
    document.getElementById('system-status').textContent = __('systemReady');
  
  // Översätt flikar
  document.querySelectorAll('.tab').forEach(tab => {
    const tabId = tab.dataset.tab;
    if (tabId) {
      tab.textContent = __(tabId);
    }
  });
  
  // Översätt rubriker med data-i18n attribut
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (key) {
      el.textContent = __(key);
    }
  });
}

// Applicera översättningar när sidan laddas
document.addEventListener('DOMContentLoaded', function() {
  // Hämta sparad språkinställning eller använd svenska som standard
  const savedLanguage = localStorage.getItem('gdial_language') || 'sv';
  currentLanguage = savedLanguage;
  document.documentElement.lang = savedLanguage;
  
  // Uppdatera språkväljaren
  if (document.getElementById('language-select')) {
    document.getElementById('language-select').value = savedLanguage;
    
    // Lägg till lyssnare på språkväljaren
    document.getElementById('language-select').addEventListener('change', function() {
      changeLanguage(this.value);
    });
  }
  
  // Applicera översättningar
  if (typeof applyTranslations === 'function') {
    applyTranslations();
  } else {
    applyBasicTranslations();
  }
});