import React, { useState, useEffect } from 'react';
import { useSettings, AppSettings } from '../hooks/useSettings';
import { useTtsVoices, TtsVoice } from '../hooks/useTtsVoices'; // Importera TtsVoice

const SettingsPage: React.FC = () => {
  const { settingsQuery, saveSettings } = useSettings();

  const [form, setForm] = useState<AppSettings>({
    ttsProvider: 'openai' as AppSettings['ttsProvider'], // Initial type
    ttsLanguage: 'sv-SE',
    ttsVoice: '',
    ttsSpeed: 1.0,
    twilioFromNumber: '',
    callTimeoutSec: 25,
    secondaryBackoffSec: 120,
    maxSecondaryAttempts: 2
  });

  // Sync när settings laddas
  useEffect(() => {
    if (settingsQuery.data) {
      setForm(settingsQuery.data);
    }
  }, [settingsQuery.data]);

  const voicesQuery = useTtsVoices(form.ttsProvider, form.ttsLanguage);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;

    // Type assertion for ttsProvider
    if (name === 'ttsProvider') {
      setForm(prev => ({ ...prev, [name]: value as AppSettings['ttsProvider'] }));
    } else {
      setForm(prev => ({ ...prev, [name]: name.includes('Sec') || name.includes('Attempts') ? Number(value) : value }));
    }
  };

  const handleSave = () => {
    saveSettings.mutate(form);
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-semibold mb-6">Inställningar</h1>

      <div className="space-y-8">
        {/* TTS Settings Section */}
        <section className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-medium mb-4">Text-to-Speech (TTS)</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="tts-provider" className="block text-sm font-medium text-gray-700 mb-1">
                TTS-leverantör
              </label>
              <select
                id="tts-provider"
                name="ttsProvider"
                value={form.ttsProvider}
                onChange={handleChange}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              >
                <option value="openai">OpenAI TTS</option>
                <option value="twilio">Twilio TTS</option>
              </select>
            </div>
            <div>
              <label htmlFor="tts-language" className="block text-sm font-medium text-gray-700 mb-1">
                Språk
              </label>
              <select
                id="tts-language"
                name="ttsLanguage"
                value={form.ttsLanguage}
                onChange={handleChange}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              >
                <option value="sv-SE">Svenska (Sverige)</option>
                <option value="en-US">Engelska (USA)</option>
                {/* Add other languages as needed */}
              </select>
            </div>
            <div>
              <label htmlFor="tts-voice" className="block text-sm font-medium text-gray-700 mb-1">
                Röst
              </label>
              <select
                id="tts-voice"
                name="ttsVoice"
                value={form.ttsVoice}
                onChange={handleChange}
                disabled={voicesQuery.isLoading}
                className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm rounded-md"
              >
                {voicesQuery.data?.map((v: TtsVoice) => (
                  <option key={v.id} value={v.id}>{v.name} ({v.gender})</option>
                ))}
              </select>
            </div>
            {/* TTS Speed */}
            <div>
              <label htmlFor="ttsSpeed" className="block text-sm font-medium text-gray-700 mb-1">Talhastighet</label>
              <input type="number" step="0.1" min="0.5" max="2" id="ttsSpeed" name="ttsSpeed" value={form.ttsSpeed}
                onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
          </div>
        </section>

        {/* Twilio / Call Settings */}
        <section className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-medium mb-4">Samtals-/SMS-inställningar</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="twilioFromNumber" className="block text-sm font-medium text-gray-700 mb-1">Twilio From-nummer</label>
              <input id="twilioFromNumber" name="twilioFromNumber" value={form.twilioFromNumber} onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
            <div>
              <label htmlFor="callTimeoutSec" className="block text-sm font-medium text-gray-700 mb-1">Call Timeout (sek)</label>
              <input type="number" id="callTimeoutSec" name="callTimeoutSec" value={form.callTimeoutSec} onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
            <div>
              <label htmlFor="secondaryBackoffSec" className="block text-sm font-medium text-gray-700 mb-1">Backoff sek.</label>
              <input type="number" id="secondaryBackoffSec" name="secondaryBackoffSec" value={form.secondaryBackoffSec} onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
            <div>
              <label htmlFor="maxSecondaryAttempts" className="block text-sm font-medium text-gray-700 mb-1">Max andra försök</label>
              <input type="number" id="maxSecondaryAttempts" name="maxSecondaryAttempts" value={form.maxSecondaryAttempts} onChange={handleChange}
                className="mt-1 block w-full border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm" />
            </div>
          </div>
        </section>

        <div className="flex justify-end">
          <button
            type="button"
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            onClick={handleSave}
          >
            Spara Inställningar
          </button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
