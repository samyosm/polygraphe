import { useTranslations } from "next-intl";
import { Tag, type TagColor } from "@/components/ui/tag";
import type { TrialStatus } from "@/lib/api/types";

const colors: Record<TrialStatus, TagColor> = {
  created: "gray",
  recording: "red",
  paused: "blue",
  completed: "green",
};

export function TrialStatusTag({ status }: { status: TrialStatus }) {
  const t = useTranslations("status");
  return (
    <Tag color={colors[status]} pulse={status === "recording"}>
      {t(status)}
    </Tag>
  );
}
