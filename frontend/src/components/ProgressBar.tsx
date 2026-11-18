interface ProgressBarProps {
  progress: number;
  status: 'pending' | 'indexing' | 'ready' | 'failed';
}

export function ProgressBar({ progress, status }: ProgressBarProps) {
  const barColor =
    status === 'failed'
      ? 'bg-red-500'
      : status === 'ready'
      ? 'bg-green-500'
      : 'bg-blue-500';

  const bgColor = status === 'failed' ? 'bg-red-900/30' : 'bg-gray-700';

  return (
    <div className={`w-full h-1.5 ${bgColor} rounded-full overflow-hidden mt-1`}>
      <div
        className={`h-full ${barColor} transition-all duration-500 ease-out`}
        style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
      />
    </div>
  );
}