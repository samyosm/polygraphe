import Image from "next/image";
import Link from "next/link";
import { getTranslations } from "next-intl/server";
import { OperatorMenu } from "@/features/operator/operator-menu";
import { isOperator } from "@/lib/api/operator";
import { BrandMark } from "./brand-mark";
import { Container } from "./container";
import { LanguageSwitcher } from "./language-switcher";

const logos = [
  { src: "/logos/un.svg", key: "un", width: 42 },
  { src: "/logos/icc.svg", key: "icc", width: 41 },
] as const;

export async function SiteHeader() {
  const [t, signedIn] = await Promise.all([
    getTranslations("header"),
    isOperator(),
  ]);

  return (
    <header className="sticky top-0 z-10 border-b border-line bg-background/90 backdrop-blur">
      <Container className="flex h-16 items-center justify-between gap-4">
        <Link
          href="/"
          aria-label={t("home")}
          className="flex items-center gap-3 text-base outline-none focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-focus"
        >
          <BrandMark className="size-8" />
          {/* The mark alone on phones, where the header is crowded. */}
          <span className="hidden sm:inline">
            <span className="font-semibold">Poly</span>Graphe
          </span>
        </Link>

        <div className="flex items-center gap-3 sm:gap-6">
          <div className="flex items-center gap-3 sm:gap-4">
            {logos.map((logo) => (
              <Image
                key={logo.key}
                src={logo.src}
                alt={t(logo.key)}
                title={t(logo.key)}
                width={logo.width}
                height={36}
                className="h-7 w-auto sm:h-9"
              />
            ))}
          </div>
          <span className="h-8 w-px bg-line" aria-hidden />
          <div className="flex items-center">
            <LanguageSwitcher />
            <OperatorMenu signedIn={signedIn} />
          </div>
        </div>
      </Container>
    </header>
  );
}
