import type { CSSProperties } from "react";

export type LogoVariant = "color" | "dark" | "mono";
export type LogoSize = "sm" | "md" | "lg" | "xl";

const SIZE_PX: Record<LogoSize, number> = {
  sm: 20,
  md: 28,
  lg: 40,
  xl: 64,
};

interface LogoProps {
  variant?: LogoVariant;
  size?: LogoSize;
  withWordmark?: boolean;
  className?: string;
  style?: CSSProperties;
  spinning?: boolean;
}

const planes: Record<LogoVariant, { body: string; fold: string; wing: string }> = {
  color: { body: "#F97316", fold: "#C2410C", wing: "#EA580C" },
  dark: { body: "#FB923C", fold: "#9A3412", wing: "#EA580C" },
  mono: { body: "currentColor", fold: "currentColor", wing: "currentColor" },
};

export function Logo({
  variant = "color",
  size = "md",
  withWordmark = true,
  className = "",
  style,
  spinning = false,
}: LogoProps) {
  const px = SIZE_PX[size];
  const c = planes[variant];
  return (
    <span
      className={`inline-flex items-center gap-2 ${className}`}
      style={style}
      aria-label="Travel System"
    >
      <svg
        width={px}
        height={px}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={spinning ? "animate-fly" : undefined}
      >
        <path d="M58 6L6 30l18 6 6 18L58 6z" fill={c.body} />
        <path d="M58 6L30 32l6 18 22-44z" fill={c.fold} />
        <path d="M58 6L30 32l10 2 18-28z" fill={c.wing} />
      </svg>
      {withWordmark && (
        <span
          className="font-semibold tracking-tight"
          style={{
            fontSize: px * 0.5,
            color: variant === "mono" ? "inherit" : undefined,
          }}
        >
          Travel System
        </span>
      )}
    </span>
  );
}

export default Logo;
