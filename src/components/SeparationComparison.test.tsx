import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { SeparationComparison } from './SeparationComparison';

test('audition switches vocals and accompaniment independently; comparison respects setup and job lock', () => {
  const onSource = vi.fn();
  const props = { hasDemucs: true, ready: true, yamnetReady: true, locked: false, source: 'original',
    onSource, onSetup: vi.fn(), onAnalyze: vi.fn(),
    data: { stems: { melband_vocals: 'v.wav', melband_instrumental: 'i.wav' },
      engine: { model: 'melband', device: 'cuda', settings: { segmentSize: 801 }, fallback: false } } };
  const view = render(<SeparationComparison {...props} />);
  fireEvent.click(screen.getByRole('button', { name: 'Mel-Band 伴奏' }));
  expect(onSource).toHaveBeenCalledWith('melband_instrumental');
  fireEvent.click(screen.getByRole('button', { name: 'Mel-Bandで分離して比較' }));
  expect(props.onAnalyze).toHaveBeenCalledOnce();
  view.rerender(<SeparationComparison {...props} locked />);
  expect(screen.getByRole('button', { name: 'Mel-Bandで分離して比較' })).toBeDisabled();
  view.rerender(<SeparationComparison {...props} yamnetReady={false} />);
  expect(screen.getByRole('button', { name: 'Mel-Bandで分離して比較' })).toBeDisabled();
  view.rerender(<SeparationComparison {...props} ready={false} />);
  fireEvent.click(screen.getByRole('button', { name: 'Mel-Bandをセットアップ' }));
  expect(props.onSetup).toHaveBeenCalledOnce();
});
