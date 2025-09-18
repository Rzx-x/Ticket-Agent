import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { text, source = 'web', user_email } = body;

    if (!text || !text.trim()) {
      return NextResponse.json(
        { error: 'Ticket text is required' },
        { status: 400 }
      );
    }

    console.log('Received ticket:', { text, source, user_email });

    // TODO: Replace this with actual backend API call
    // const backendResponse = await fetch('http://your-backend-api/tickets', {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //   },
    //   body: JSON.stringify({
    //     text,
    //     source,
    //     user_email
    //   }),
    // });

    // For now, return mock response
    const mockResponse = {
      id: `TK-${Date.now()}`,
      source,
      text,
      language: detectLanguage(text),
      category: classifyIssue(text),
      urgency: determineUrgency(text),
      ai_response: generateMockResponse(text),
      status: 'open',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      user_email,
    };

    return NextResponse.json(mockResponse);

  } catch (error) {
    console.error('Error processing ticket:', error);
    return NextResponse.json(
      { error: 'Failed to process ticket' },
      { status: 500 }
    );
  }
}

// Mock helper functions - replace with actual AI logic
function detectLanguage(text: string): string {
  // Simple language detection - replace with actual TensorFlow.js model
  const hindiWords = ['nahi', 'hai', 'kya', 'kaise', 'mein', 'ko', 'se', 'aur', 'kaam', 'chal'];
  const hasHindi = hindiWords.some(word => text.toLowerCase().includes(word));
  return hasHindi ? 'Hindi+English' : 'English';
}

function classifyIssue(text: string): string {
  const lowerText = text.toLowerCase();
  
  if (lowerText.includes('vpn') || lowerText.includes('network') || lowerText.includes('wifi') || lowerText.includes('internet')) {
    return 'Network/VPN';
  } else if (lowerText.includes('email') || lowerText.includes('mail')) {
    return 'Email';
  } else if (lowerText.includes('laptop') || lowerText.includes('computer') || lowerText.includes('hardware')) {
    return 'Hardware';
  } else if (lowerText.includes('software') || lowerText.includes('application') || lowerText.includes('app')) {
    return 'Software';
  } else if (lowerText.includes('password') || lowerText.includes('login') || lowerText.includes('access')) {
    return 'Account Access';
  } else {
    return 'General Support';
  }
}

function determineUrgency(text: string): 'Low' | 'Medium' | 'High' | 'Critical' {
  const lowerText = text.toLowerCase();
  
  if (lowerText.includes('urgent') || lowerText.includes('critical') || lowerText.includes('down') || lowerText.includes('emergency')) {
    return 'Critical';
  } else if (lowerText.includes('important') || lowerText.includes('asap') || lowerText.includes('quickly')) {
    return 'High';
  } else if (lowerText.includes('when possible') || lowerText.includes('sometime')) {
    return 'Low';
  } else {
    return 'Medium';
  }
}

function generateMockResponse(text: string): string {
  const category = classifyIssue(text);
  const hasHindi = detectLanguage(text).includes('Hindi');
  
  const responses = {
    'Network/VPN': {
      en: "I understand you're having VPN/network issues. Here are some quick steps to try:\n\n1. Restart your VPN client\n2. Check your internet connection\n3. Try connecting to a different VPN server\n4. Clear your DNS cache\n\nIf these don't help, I'm escalating this to our network team who will contact you within 30 minutes.",
      hi: "मैं समझ गया कि आपको VPN/network की समस्या है। ये steps try करें:\n\n1. VPN client restart करें\n2. Internet connection check करें\n3. Different VPN server try करें\n4. DNS cache clear करें\n\nअगर ये काम नहीं करता, तो मैं इसे network team को भेज रहा हूं, वो 30 मिनट में contact करेंगे।"
    },
    'Email': {
      en: "I see you're having email issues. Let's try these solutions:\n\n1. Check your internet connection\n2. Restart your email client (Outlook/Thunderbird)\n3. Verify your email settings\n4. Check if the email server is down\n\nI'm also notifying our email administration team to investigate any server-side issues.",
      hi: "Email की problem है। ये solutions try करें:\n\n1. Internet connection check करें\n2. Email client restart करें (Outlook/Thunderbird)\n3. Email settings verify करें\n4. Email server down तो नहीं, check करें\n\nEmail administration team को भी inform कर रहा हूं server-side issues check करने के लिए।"
    },
    default: {
      en: "Thank you for contacting IT support. I've recorded your request and our team will review it shortly. Based on the information provided, I'm categorizing this as a " + category + " issue.\n\nYou can expect a response from our specialized team within 2 hours during business hours.",
      hi: "IT support contact करने के लिए धन्यवाद। आपकी request record हो गई है और हमारी team जल्दी इसे देखेगी। दी गई जानकारी के आधार पर, मैं इसे " + category + " issue categorize कर रहा हूं।\n\nBusiness hours में 2 घंटे के अंदर specialized team का response मिलेगा।"
    }
  };
  
  const responseSet = responses[category as keyof typeof responses] || responses.default;
  return hasHindi ? responseSet.hi : responseSet.en;
}