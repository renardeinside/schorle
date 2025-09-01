import { Space_Mono } from "next/font/google";
import Image from "next/image";

export const spaceMono = Space_Mono({
  subsets: ["latin"],
  weight: ["400", "700"],
});

export default function Logo({
  className,
  width = 40,
  height = 40,
}: {
  className?: string;
  width?: number;
  height?: number;
}) {
  return (
    <div className={className}>
      <Image src="/logo.svg" alt="Logo" width={width} height={height} />
      <span className={spaceMono.className}>Schorle</span>
    </div>
  );
}
