/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import App from '../App';

jest.mock('react-native-image-picker', () => ({
  launchImageLibrary: jest.fn(),
}));

global.fetch = jest.fn(url => {
  if (String(url).includes('/profile/preferences')) {
    return Promise.resolve({
      ok: true,
      json: async () => ({
        display_name: '',
        work_start_time: '09:00',
        work_end_time: '18:00',
        planning_style: 'balanced',
        priority_preference: 'balanced',
        peak_focus_period: 'morning',
        max_daily_focus_hours: 6,
        preferred_task_duration_hours: 2,
        break_interval_minutes: 90,
        avoid_time_ranges: [],
      }),
    });
  }

  return Promise.resolve({
    ok: true,
    json: async () => [],
  });
});

test('renders correctly', async () => {
  await ReactTestRenderer.act(() => {
    ReactTestRenderer.create(<App />);
  });
});
