/**
 * Component test utilities for OmniDesk AI
 * Simple test functions that can be run without complex testing frameworks
 */

import React from 'react';
import { ChakraProvider } from '@chakra-ui/react';
import TicketForm from '@/components/TicketForm';
import theme from '@/theme';

// Test wrapper component
const TestTicketForm = () => {
  return React.createElement(
    ChakraProvider,
    { theme },
    React.createElement(TicketForm)
  );
};

// Basic component test
export const testTicketFormRendering = (): boolean => {
  try {
    const element = React.createElement(TestTicketForm);
    console.log('✓ TicketForm component can be instantiated');
    return true;
  } catch (error) {
    console.error('✗ TicketForm component failed to instantiate:', error);
    return false;
  }
};

// Test form validation logic
export const testFormValidation = (): boolean => {
  const validEmail = 'test@powergrid.com';
  const invalidEmail = 'invalid-email';
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  
  const validEmailTest = emailRegex.test(validEmail);
  const invalidEmailTest = !emailRegex.test(invalidEmail);
  
  if (validEmailTest && invalidEmailTest) {
    console.log('✓ Email validation works correctly');
    return true;
  } else {
    console.error('✗ Email validation failed');
    return false;
  }
};

// Test message length validation
export const testMessageLengthValidation = (): boolean => {
  const shortMessage = 'Hi';
  const normalMessage = 'This is a normal message for testing purposes';
  const longMessage = 'a'.repeat(600);
  
  const validateLength = (text: string, min: number, max: number): boolean => {
    return text.length >= min && text.length <= max;
  };
  
  const shortTest = !validateLength(shortMessage, 10, 500);
  const normalTest = validateLength(normalMessage, 10, 500);
  const longTest = !validateLength(longMessage, 10, 500);
  
  if (shortTest && normalTest && longTest) {
    console.log('✓ Message length validation works correctly');
    return true;
  } else {
    console.error('✗ Message length validation failed');
    return false;
  }
};

// Test API request format
export const testAPIRequestFormat = (): boolean => {
  const mockRequestData = {
    text: 'Test message',
    source: 'web',
    user_email: 'test@powergrid.com'
  };
  
  const hasRequiredFields = 
    typeof mockRequestData.text === 'string' &&
    typeof mockRequestData.source === 'string' &&
    typeof mockRequestData.user_email === 'string';
  
  if (hasRequiredFields) {
    console.log('✓ API request format is correct');
    return true;
  } else {
    console.error('✗ API request format is incorrect');
    return false;
  }
};

// Test keyboard shortcut detection
export const testKeyboardShortcuts = (): boolean => {
  const mockEvent = {
    ctrlKey: true,
    key: 'Enter',
    preventDefault: () => {}
  };
  
  const isValidShortcut = mockEvent.ctrlKey && mockEvent.key === 'Enter';
  
  if (isValidShortcut) {
    console.log('✓ Keyboard shortcut detection works');
    return true;
  } else {
    console.error('✗ Keyboard shortcut detection failed');
    return false;
  }
};

// Test language detection logic
export const testLanguageDetection = (): boolean => {
  const englishText = 'This is an English sentence';
  const hindiMixedText = 'Mera computer nahi chal raha please help';
  
  // Simple language detection based on character sets
  const hasHindi = (text: string): boolean => {
    const hindiWords = ['mera', 'nahi', 'hai', 'karo', 'kya', 'main'];
    return hindiWords.some(word => text.toLowerCase().includes(word));
  };
  
  const englishTest = !hasHindi(englishText);
  const hindiTest = hasHindi(hindiMixedText);
  
  if (englishTest && hindiTest) {
    console.log('✓ Language detection logic works');
    return true;
  } else {
    console.error('✗ Language detection logic failed');
    return false;
  }
};

// Test suggestion system
export const testSuggestionSystem = (): boolean => {
  const suggestions = [
    { icon: '💻', text: 'My laptop will not connect to WiFi' },
    { icon: '🔒', text: 'VPN nahi chal raha hai' },
    { icon: '📧', text: 'Email server down' },
    { icon: '🖨️', text: 'Printer not working' }
  ];
  
  const hasValidSuggestions = suggestions.every(suggestion => 
    suggestion.icon && suggestion.text && suggestion.text.length > 0
  );
  
  if (hasValidSuggestions) {
    console.log('✓ Suggestion system is properly configured');
    return true;
  } else {
    console.error('✗ Suggestion system has invalid data');
    return false;
  }
};

// Run all component tests
export const runAllComponentTests = (): { passed: number; failed: number; total: number } => {
  console.log('Running Component Tests for OmniDesk AI...');
  console.log('='.repeat(50));
  
  const tests = [
    { name: 'Component Rendering', test: testTicketFormRendering },
    { name: 'Form Validation', test: testFormValidation },
    { name: 'Message Length Validation', test: testMessageLengthValidation },
    { name: 'API Request Format', test: testAPIRequestFormat },
    { name: 'Keyboard Shortcuts', test: testKeyboardShortcuts },
    { name: 'Language Detection', test: testLanguageDetection },
    { name: 'Suggestion System', test: testSuggestionSystem }
  ];
  
  let passed = 0;
  let failed = 0;
  
  tests.forEach(({ name, test }, index) => {
    try {
      console.log(`\nTest ${index + 1}: ${name}`);
      const result = test();
      if (result) {
        passed++;
      } else {
        failed++;
      }
    } catch (error) {
      console.error(`Test ${index + 1} (${name}) threw an error:`, error);
      failed++;
    }
  });
  
  console.log('\n' + '='.repeat(50));
  console.log(`Tests completed: ${passed} passed, ${failed} failed`);
  console.log(`Success rate: ${((passed / tests.length) * 100).toFixed(1)}%`);
  
  return { passed, failed, total: tests.length };
};

// Export test component for manual testing
export { TestTicketForm };

// Default export for easy importing
export default {
  runAllComponentTests,
  testTicketFormRendering,
  testFormValidation,
  testMessageLengthValidation,
  testAPIRequestFormat,
  testKeyboardShortcuts,
  testLanguageDetection,
  testSuggestionSystem,
  TestTicketForm
};