/**
 * ProgressTracker Component
 *
 * Displays pipeline progress messages during job search execution.
 * Shows the current phase and a message indicating the process may take time.
 */

import type { PipelinePhase } from "../../types";

const PHASE_MESSAGES: Record<PipelinePhase, string> = {
  profiling: "2/6 Creating profile...",
  searching: "3/6 Searching jobs...",
  scoring: "4/6 Scoring jobs...",
  analyzing: "5/6 Analyzing jobs...",
  generating: "6/6 Generating...",
};

interface ProgressTrackerProps {
  currentPhase: PipelinePhase | null;
}

export default function ProgressTracker({
  currentPhase,
}: ProgressTrackerProps) {
  return (
    <>
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        {currentPhase && PHASE_MESSAGES[currentPhase]
          ? PHASE_MESSAGES[currentPhase]
          : "1/6 Starting search..."}
      </h3>
    </>
  );
}
