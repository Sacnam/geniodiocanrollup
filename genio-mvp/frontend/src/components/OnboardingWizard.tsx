import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, ChevronLeft, Check, BookOpen, Brain, Zap, Mail } from 'lucide-react';

interface OnboardingData {
  interests: string[];
  feeds: string[];
  briefTime: string;
  timezone: string;
  budget: number;
}

const INTEREST_OPTIONS = [
  'Technology', 'Science', 'Business', 'Design', 'Programming',
  'AI & ML', 'Productivity', 'Health', 'Finance', 'Politics',
  'Environment', 'Education', 'Arts', 'Sports'
];

const SUGGESTED_FEEDS = [
  { id: '1', name: 'TechCrunch', category: 'Technology', url: 'https://techcrunch.com/feed/' },
  { id: '2', name: 'MIT Technology Review', category: 'Technology', url: 'https://www.technologyreview.com/feed/' },
  { id: '3', name: 'Nature News', category: 'Science', url: 'https://www.nature.com/news/rss' },
  { id: '4', name: 'Harvard Business Review', category: 'Business', url: 'https://hbr.org/rss' },
  { id: '5', name: 'Product Hunt', category: 'Technology', url: 'https://www.producthunt.com/feed' },
  { id: '6', name: 'ArXiv AI', category: 'AI & ML', url: 'http://arxiv.org/rss/cs.AI' },
];

export const OnboardingWizard: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [data, setData] = useState<OnboardingData>({
    interests: [],
    feeds: [],
    briefTime: '08:00',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    budget: 3,
  });

  const steps = [
    { title: 'Welcome', icon: Zap },
    { title: 'Interests', icon: Brain },
    { title: 'Feeds', icon: BookOpen },
    { title: 'Brief', icon: Mail },
    { title: 'Complete', icon: Check },
  ];

  const toggleInterest = (interest: string) => {
    setData(prev => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter(i => i !== interest)
        : [...prev.interests, interest]
    }));
  };

  const toggleFeed = (feedId: string) => {
    setData(prev => ({
      ...prev,
      feeds: prev.feeds.includes(feedId)
        ? prev.feeds.filter(f => f !== feedId)
        : [...prev.feeds, feedId]
    }));
  };

  const handleComplete = async () => {
    // TODO: Save preferences to API
    // TODO: Subscribe to selected feeds
    navigate('/feeds');
  };

  const renderStep = () => {
    switch (step) {
      case 0:
        return (
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mx-auto">
              <Zap className="w-10 h-10 text-purple-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Welcome to Genio
              </h2>
              <p className="text-gray-600 max-w-md mx-auto">
                Your AI-powered knowledge assistant. Let's set up your personalized experience in just a few steps.
              </p>
            </div>
            <div className="flex justify-center gap-8 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4" />
                <span>Smart Aggregation</span>
              </div>
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4" />
                <span>AI Insights</span>
              </div>
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-bold text-gray-900 mb-2">What are you interested in?</h2>
              <p className="text-gray-600">Select topics to personalize your content</p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {INTEREST_OPTIONS.map(interest => (
                <button
                  key={interest}
                  onClick={() => toggleInterest(interest)}
                  className={`px-4 py-2 rounded-full border-2 transition-all ${
                    data.interests.includes(interest)
                      ? 'border-purple-600 bg-purple-50 text-purple-700'
                      : 'border-gray-200 hover:border-purple-300'
                  }`}
                >
                  {interest}
                </button>
              ))}
            </div>
            <p className="text-center text-sm text-gray-500">
              {data.interests.length} topics selected
            </p>
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h2 className="text-xl font-bold text-gray-900 mb-2">Add some feeds</h2>
              <p className="text-gray-600">Start with popular sources or skip and add later</p>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {SUGGESTED_FEEDS.map(feed => (
                <button
                  key={feed.id}
                  onClick={() => toggleFeed(feed.id)}
                  className={`w-full p-3 rounded-lg border-2 text-left transition-all flex items-center justify-between ${
                    data.feeds.includes(feed.id)
                      ? 'border-purple-600 bg-purple-50'
                      : 'border-gray-200 hover:border-purple-300'
                  }`}
                >
                  <div>
                    <p className="font-medium text-gray-900">{feed.name}</p>
                    <p className="text-sm text-gray-500">{feed.category}</p>
                  </div>
                  {data.feeds.includes(feed.id) && (
                    <Check className="w-5 h-5 text-purple-600" />
                  )}
                </button>
              ))}
            </div>
            <p className="text-center text-sm text-gray-500">
              {data.feeds.length} feeds selected
            </p>
          </div>
        );

      case 3:
        return (
          <div className="space-y-6 max-w-md mx-auto">
            <div className="text-center">
              <h2 className="text-xl font-bold text-gray-900 mb-2">Configure your Daily Brief</h2>
              <p className="text-gray-600">Get a personalized summary delivered daily</p>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Delivery Time
                </label>
                <input
                  type="time"
                  value={data.briefTime}
                  onChange={(e) => setData(prev => ({ ...prev, briefTime: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Monthly AI Budget (${data.budget})
                </label>
                <input
                  type="range"
                  min="0"
                  max="10"
                  step="1"
                  value={data.budget}
                  onChange={(e) => setData(prev => ({ ...prev, budget: parseInt(e.target.value) }))}
                  className="w-full"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Higher budget = more AI-powered insights
                </p>
              </div>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="text-center space-y-6">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <Check className="w-10 h-10 text-green-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                You're all set!
              </h2>
              <p className="text-gray-600 max-w-md mx-auto">
                Your personalized knowledge workspace is ready. We'll start gathering content based on your preferences.
              </p>
            </div>
            <div className="bg-gray-50 rounded-lg p-4 max-w-sm mx-auto text-left space-y-2">
              <p className="text-sm"><strong>{data.interests.length}</strong> interests selected</p>
              <p className="text-sm"><strong>{data.feeds.length}</strong> feeds subscribed</p>
              <p className="text-sm">Daily brief at <strong>{data.briefTime}</strong></p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-white rounded-2xl shadow-xl p-8">
        {/* Progress */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            {steps.map((s, i) => (
              <div key={i} className="flex items-center">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                  i <= step ? 'bg-purple-600 text-white' : 'bg-gray-200 text-gray-500'
                }`}>
                  <s.icon className="w-5 h-5" />
                </div>
                {i < steps.length - 1 && (
                  <div className={`w-16 h-1 mx-2 transition-colors ${
                    i < step ? 'bg-purple-600' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
          <div className="text-center text-sm text-gray-500">
            Step {step + 1} of {steps.length}: {steps[step].title}
          </div>
        </div>

        {/* Content */}
        <div className="mb-8 min-h-[300px] flex items-center">
          {renderStep()}
        </div>

        {/* Navigation */}
        <div className="flex justify-between">
          <button
            onClick={() => setStep(Math.max(0, step - 1))}
            disabled={step === 0}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-5 h-5" />
            Back
          </button>

          {step < steps.length - 1 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="flex items-center gap-2 px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Next
              <ChevronRight className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={handleComplete}
              className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Get Started
              <Check className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
