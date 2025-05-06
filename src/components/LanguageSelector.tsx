import React from 'react';
import { Language } from '../types';

interface LanguageSelectorProps {
  onSelectLanguage: (language: Language) => void;
  currentLanguage: Language | null;
}

export function LanguageSelector({ onSelectLanguage, currentLanguage }: LanguageSelectorProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
        <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
          Select Language
        </h2>
        <select
          value={currentLanguage || ''}
          onChange={(e) => onSelectLanguage(e.target.value as Language)}
          className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
        >
          <option value="">Select a language</option>
          <option value="english">English</option>
          <option value="tamil">தமிழ் (Tamil)</option>
          <option value="hindi">हिंदी (Hindi)</option>
          <option value="telugu">తెలుగు (Telugu)</option>
        </select>
      </div>
    </div>
  );
}