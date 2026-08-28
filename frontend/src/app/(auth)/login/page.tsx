"use client";

import Image from "next/image";
import Link from "next/link";
import { CloudCog, Code2, Gauge, Sparkles } from "lucide-react";
import { motion, useReducedMotion } from "framer-motion";

import { LoginForm } from "@/components/auth/login-form";

export default function LoginPage() {
  const reduceMotion = useReducedMotion();

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
        className="fixed inset-0 bg-[linear-gradient(180deg,rgba(250,248,255,.58),rgba(250,248,255,.80)_68%,rgba(250,248,255,.95)),radial-gradient(circle_at_18%_35%,rgba(255,255,255,.18),transparent_42%)] dark:bg-[linear-gradient(90deg,rgba(7,5,13,.32),rgba(7,5,13,.50)_52%,rgba(7,5,13,.88)),radial-gradient(circle_at_18%_35%,rgba(37,99,235,.08),transparent_40%)]"
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

        <div className="auth-content grid flex-1 items-center gap-8 py-9 lg:grid-cols-[minmax(0,1.12fr)_minmax(24rem,.78fr)] lg:gap-12 lg:py-3 xl:gap-20">
          <motion.section
            initial={reduceMotion ? false : { opacity: 0, x: -28 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.65, ease: "easeOut" }}
            className="auth-hero flex min-h-[18rem] flex-col justify-end"
          >
            <motion.div
              animate={reduceMotion ? undefined : { y: [0, -7, 0], rotate: [0, 1.5, 0] }}
              transition={{ duration: 4.8, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
              className="mb-5 flex w-fit items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--card)] px-4 py-2 text-xs font-black uppercase tracking-[.16em] shadow-xl backdrop-blur-xl"
            >
              <Sparkles className="size-3.5 text-[var(--primary)]" />
              Welcome back, builder
            </motion.div>

            <div className="max-w-2xl rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 shadow-2xl backdrop-blur-2xl sm:p-8 lg:bg-[color-mix(in_srgb,var(--card)_78%,transparent)]">
              <h1 className="max-w-xl text-4xl font-black leading-[1.02] tracking-[-.045em] sm:text-5xl xl:text-6xl">
                Continue turning ideas into <span className="text-[var(--primary)]">clear infrastructure.</span>
              </h1>
              <p className="mt-5 max-w-xl text-sm font-medium leading-7 text-[var(--muted-foreground)] sm:text-base">
                Return to your analyses, performance evidence, and USD cost intelligence—all in one workspace.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <span className="flex items-center gap-2 rounded-2xl border border-[var(--border)] bg-[var(--background)]/70 px-4 py-3 text-xs font-extrabold shadow-lg backdrop-blur-md">
                  <CloudCog className="size-4 text-cyan-700 dark:text-cyan-200" /> Cloud architecture
                </span>
                <span className="flex items-center gap-2 rounded-2xl border border-[var(--border)] bg-[var(--background)]/70 px-4 py-3 text-xs font-extrabold shadow-lg backdrop-blur-md">
                  <Gauge className="size-4 text-violet-700 dark:text-violet-200" /> Live performance
                </span>
              </div>
            </div>
          </motion.section>

          <motion.section
            initial={reduceMotion ? false : { opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ delay: reduceMotion ? 0 : 0.15, duration: 0.55, ease: "easeOut" }}
            className="mx-auto w-full max-w-[30rem]"
          >
            <div className="rounded-[2rem] border border-[var(--border)] bg-[var(--card)] p-6 shadow-[0_30px_90px_-35px_rgba(50,20,90,.55)] backdrop-blur-2xl sm:p-8 dark:shadow-[0_30px_90px_-35px_rgba(34,211,238,.35)]">
              <div className="mb-7">
                <div className="flex items-center gap-2 text-xs font-black uppercase tracking-[.18em] text-[var(--primary)]">
                  <Sparkles className="size-3.5" />
                  Welcome back
                </div>
                <h2 className="mt-2 text-3xl font-black tracking-tight sm:text-4xl">Sign in to your workspace</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted-foreground)]">
                  Continue your infrastructure analyses and reports.
                </p>
              </div>

              <LoginForm />
            </div>
          </motion.section>
        </div>
      </div>
    </main>
  );
}
