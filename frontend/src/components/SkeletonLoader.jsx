import React from 'react';

export function ShowcaseSkeleton() {
  return (
    <div className="space-y-6 max-w-6xl mx-auto animate-pulse">
      {/* Header Banner Skeleton */}
      <div className="h-40 rounded-2xl bg-slate-900/60 border border-slate-800/80 p-6 flex flex-col justify-between">
        <div className="space-y-3">
          <div className="h-4 w-44 rounded-md bg-slate-800" />
          <div className="h-7 w-80 rounded-lg bg-slate-800" />
          <div className="h-4 w-3/4 rounded-md bg-slate-800/70" />
        </div>
      </div>

      {/* 2 Case Cards Skeleton */}
      {[1, 2].map((i) => (
        <div
          key={i}
          className="rounded-2xl bg-slate-900/60 border border-slate-800/80 p-6 space-y-4"
        >
          <div className="flex items-center justify-between pb-3 border-b border-slate-800/60">
            <div className="h-6 w-48 rounded-full bg-slate-800" />
            <div className="h-5 w-64 rounded-lg bg-slate-800" />
          </div>
          <div className="h-4 w-full rounded bg-slate-800/70" />
          <div className="h-12 w-full rounded-xl bg-slate-950/60 border border-slate-800/40" />

          {/* Dual Evidence Box */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="h-36 rounded-xl bg-slate-950/60 border border-slate-800/60 p-4 space-y-2">
              <div className="h-4 w-32 rounded bg-slate-800" />
              <div className="h-8 w-24 rounded bg-slate-800" />
              <div className="h-10 w-full rounded bg-slate-900/60" />
            </div>
            <div className="h-36 rounded-xl bg-slate-950/60 border border-slate-800/60 p-4 space-y-2">
              <div className="h-4 w-32 rounded bg-slate-800" />
              <div className="h-8 w-24 rounded bg-slate-800" />
              <div className="h-10 w-full rounded bg-slate-900/60" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function FactsGridSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-pulse">
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          className="rounded-2xl bg-slate-900/60 border border-slate-800/80 p-5 space-y-4 flex flex-col justify-between"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="h-4 w-28 rounded bg-slate-800" />
              <div className="h-4 w-12 rounded bg-slate-800" />
            </div>
            <div className="h-3 w-20 rounded bg-slate-800/60" />
            <div className="h-5 w-48 rounded bg-slate-800" />
            <div className="h-8 w-24 rounded bg-slate-800" />
            <div className="flex gap-1.5 pt-1">
              <div className="h-5 w-20 rounded bg-slate-800/60" />
              <div className="h-5 w-16 rounded bg-slate-800/60" />
            </div>
          </div>

          <div className="pt-3 border-t border-slate-800/60 space-y-2">
            <div className="h-12 w-full rounded-xl bg-slate-950/60 border border-slate-800/40" />
            <div className="flex justify-between">
              <div className="h-3 w-20 rounded bg-slate-800/50" />
              <div className="h-3 w-24 rounded bg-slate-800/50" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function MatrixSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="rounded-2xl bg-slate-900/60 border border-slate-800/80 p-5 space-y-4"
        >
          <div className="flex justify-between items-center pb-3 border-b border-slate-800/60">
            <div className="h-6 w-40 rounded-full bg-slate-800" />
            <div className="h-5 w-32 rounded-full bg-slate-800/60" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="h-32 rounded-xl bg-slate-950/60 border border-slate-800/60 p-3 space-y-2">
              <div className="h-4 w-28 rounded bg-slate-800" />
              <div className="h-6 w-20 rounded bg-slate-800" />
              <div className="h-8 w-full rounded bg-slate-900/60" />
            </div>
            <div className="h-32 rounded-xl bg-slate-950/60 border border-slate-800/60 p-3 space-y-2">
              <div className="h-4 w-28 rounded bg-slate-800" />
              <div className="h-6 w-20 rounded bg-slate-800" />
              <div className="h-8 w-full rounded bg-slate-900/60" />
            </div>
          </div>

          <div className="h-12 rounded-xl bg-slate-950/60 border border-slate-800/40" />
        </div>
      ))}
    </div>
  );
}

export function DocumentListSkeleton() {
  return (
    <div className="divide-y divide-slate-800/60 animate-pulse">
      {[1, 2, 3].map((i) => (
        <div key={i} className="py-4 flex items-center justify-between px-3">
          <div className="flex items-center space-x-3.5">
            <div className="h-10 w-10 rounded-xl bg-slate-800 flex-shrink-0" />
            <div className="space-y-2">
              <div className="h-4 w-48 rounded bg-slate-800" />
              <div className="h-3 w-64 rounded bg-slate-800/60" />
              <div className="h-3 w-36 rounded bg-slate-800/40" />
            </div>
          </div>
          <div className="h-8 w-8 rounded-lg bg-slate-800" />
        </div>
      ))}
    </div>
  );
}
