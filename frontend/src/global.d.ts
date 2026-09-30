import type { Locale } from "@/i18n/config";
import type messages from "@/i18n/messages/en.json";

// Makes translation keys type-checked against the English messages.
declare module "next-intl" {
  interface AppConfig {
    Locale: Locale;
    Messages: typeof messages;
  }
}
