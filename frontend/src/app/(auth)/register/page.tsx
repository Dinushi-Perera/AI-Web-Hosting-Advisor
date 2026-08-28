"use client";

import Image from "next/image";
import Link from "next/link";
import {
  Braces,
  CloudCog,
  Code2,
  DollarSign,
  ServerCog,
  Sparkles,
} from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import { RegisterForm } from "@/components/auth/register-form";

const engineeringSignals = [
  { icon: CloudCog, label: "Cloud architecture", tone: "text-cyan-700 dark:text-cyan-200" },
  { icon: ServerCog, label: "Performance evidence", tone: "text-violet-700 dark:text-violet-200" },
  { icon: DollarSign, label: "USD cost clarity", tone: "text-amber-700 dark:text-amber-200" },
];

export default function RegisterPage() {
  const reduceMotion = useReducedMotion();

  const floating = (delay: number, distance = 8) =>
    reduceMotion
      ? {}
      : {
          animate: { y: [0, -distance, 0], rotate: [0, 1.5, 0] },
          transition: {
            delay,
            duration: 4.8,
            ease: "easeInOut" as const,
            repeat: Number.POSITIVE_INFINITY,
          },
        };

  return (
    <main className="auth-viewport fixed inset-0 z-50 overflow-y-auto bg-[var(--background)] text-[var(--foreground)]">
      <motion.div
        aria-hidden="true"
        className="fixed -inset-6"
        animate={reduceMotion ? undefined : { scale: [1.03, 1.075, 1.03], x: [0, -8, 0] }}
        transition={{ duration: 18, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
      >
        <Image
          src="/images/create-account-engineering-lab-v2.png"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover object-[43%_center] lg:object-center"
        />
      </motion.div>

      <div
        aria-hidden="true"
        className="fixed inset-0 bg-[linear-gradient(180deg,rgba(250,248,255,.60),rgba(250,248,255,.82)_68%,rgba(250,248,255,.96)),radial-gradient(circle_at_18%_35%,rgba(255,255,255,.18),transparent_42%)] dark:bg-[linear-gradient(90deg,rgba(7,5,13,.34),rgba(7,5,13,.52)_52%,rgba(7,5,13,.88)),radial-gradient(circle_at_18%_35%,rgba(37,99,235,.08),transparent_40%)]"
      />
      <motion.div
        aria-hidden="true"
        className="fixed -left-28 top-1/3 size-80 rounded-full bg-violet-400/15 blur-3xl dark:bg-violet-500/10"
        animate={reduceMotion ? undefined : { x: [0, 36, 0], y: [0, -22, 0] }}
        transition={{ duration: 12, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
      />
      <motion.div
        aria-hidden="true"
        className="fixed -right-20 bottom-0 size-72 rounded-full bg-cyan-300/20 blur-3xl dark:bg-cyan-500/10"
        animate={reduceMotion ? undefined : { x: [0, -24, 0], y: [0, -30, 0] }}
        transition={{ duration: 14, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
      />

      <div className="auth-shell relative mx-auto flex min-h-screen w-full max-w-[100rem] flex-col px-4 py-4 sm:px-7 sm:py-6 lg:px-10 lg:py-4">
        <header className="flex shrink-0 items-center">
          <Link
            href="/"
            className="group flex items-center gap-3 rounded-full border border-[var(--border)] bg-[var(--card)] px-3 py-2 shadow-lg backdrop-blur-xl transition-transform hover:-translate-y-0.5"
          >
            <span className="grid size-9 place-items-center rounded-full bg-[var(--primary)] text-[var(--primary-foreground)] shadow-md">
              <Code2 className="size-4" />
            </span>
            <span className="hidden text-sm font-black tracking-tight sm:block">AI Hosting Advisor</span>
          </Link>

        </header>

        <div className="auth-content grid flex-1 items-center gap-8 py-9 lg:grid-cols-[minmax(0,1.12fr)_minmax(25rem,.78fr)] lg:gap-12 lg:py-3 xl:gap-20">
          <motion.section
            initial={reduceMotion ? false : { opacity: 0, x: -28 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.65, ease: "easeOut" }}
            className="auth-hero flex min-h-[18rem] flex-col justify-end"
          >
            <motion.div
              {...floating(0.2, 7)}
              className="mb-5 flex w-fit items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--card)] px-4 py-2 text-xs font-black uppercase tracking-[.16em] shadow-xl backdrop-blur-xl"
            >
              <Sparkles className="size-3.5 text-[var(--primary)]" />
              Built for software teams
            </motion.div>

            <div className="max-w-2xl rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 shadow-2xl backdrop-blur-2xl sm:p-8 lg:bg-[color-mix(in_srgb,var(--card)_78%,transparent)]">
              <h1 className="max-w-xl text-4xl font-black leading-[1.02] tracking-[-.045em] sm:text-5xl xl:text-6xl">
                Build confidently. <span className="text-[var(--primary)]">Host intelligently.</span>
              </h1>
              <p className="mt-5 max-w-xl text-sm font-medium leading-7 text-[var(--muted-foreground)] sm:text-base">
                Create your workspace for clear infrastructure recommendations, explainable performance insights, and USD-only cost guidance.
              </p>

              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                {engineeringSignals.map(({ icon: Icon, label, tone }, index) => (
                  <motion.div
                    key={label}
                    {...floating(0.6 + index * 0.35, 5 + index)}
                    className="flex items-center gap-2.5 rounded-2xl border border-[var(--border)] bg-[var(--background)]/70 px-3 py-3 text-xs font-extrabold shadow-lg backdrop-blur-md"
                  >
                    <Icon className={`size-4 shrink-0 ${tone}`} />
                    {label}
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.section>

          <motion.section
            initial={reduceMotion ? false : { opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: reduceMotion ? 0 : 0.15, duration: 0.55, ease: "easeOut" }}
            className="relative mx-auto w-full max-w-[31rem]"
          >
            <motion.div
              {...floating(0.8, 7)}
              aria-hidden="true"
              className="absolute -left-5 top-14 z-10 hidden size-12 place-items-center rounded-2xl border border-[var(--border)] bg-[var(--card)] text-[var(--primary)] shadow-xl backdrop-blur-xl sm:grid"
            >
              <Braces className="size-5" />
            </motion.div>

            <div className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-5 shadow-[0_30px_90px_-35px_rgba(50,20,90,.55)] backdrop-blur-2xl sm:p-7 lg:p-5 xl:p-7 dark:shadow-[0_30px_90px_-35px_rgba(34,211,238,.35)]">
              <div className="mb-5">
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-[.18em] text-[var(--primary)]">
                  <Sparkles className="size-3.5" />
                  Create workspace
                </div>
                <h2 className="mt-2 text-3xl font-black tracking-tight xl:text-4xl">Start building smarter</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted-foreground)]">
                  Set up your account and begin your first hosting analysis.
                </p>
              </div>

              <RegisterForm />
            </div>
          </motion.section>
        </div>
      </div>
    </main>
  );
}
