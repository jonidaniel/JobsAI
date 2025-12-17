/**
 * ProgressTracker Component
 *
 * Displays pipeline progress messages during job search execution.
 * Shows the current phase and a message indicating the process may take time.
 */

import type { PipelinePhase } from "../../types";

const PHASE_MESSAGES: Record<PipelinePhase, string> = {
  profiling: "2/6 Creating your profile...",
  searching: "3/6 Searching for jobs...",
  scoring: "4/6 Scoring the jobs...",
  analyzing: "5/6 Doing analysis...",
  generating: "6/6 Generating cover letters...",
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
      <h3 className="text-base sm:text-xl md:text-2xl lg:text-3xl font-semibold text-white text-center">
        This might take a few minutes
      </h3>
    </>
  );
}
