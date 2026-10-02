"use client";

import type {
    SubagentErrorEvent,
    SubagentFinishedEvent,
    SubagentStartedEvent,
} from "@ag-ui/client";
import { useAgent } from "@copilotkit/react-core/v2";
import { useEffect, useState } from "react";

// The shape of the state this backend shares; the protocol itself leaves `State` untyped.
type SharedState = {
    favorites?: string[];
    location?: { name?: string; country?: string; region?: string };
};

/**
 * Two things the AG-UI 1.0 protocol carries besides the chat: the sub-agents the agent
 * delegates to (SUBAGENT_* events) and the shared state (STATE_SNAPSHOT), which here
 * holds the favorite cities and the last resolved location.
 */
export function AgentPanel() {
    const { agent } = useAgent({ agentId: "agenticChatAgent" });
    // The events are kept as the protocol sends them. A run is running until a finished or
    // error event with its `subagentRunId` arrives, so no separate run record is needed.
    const [started, setStarted] = useState<SubagentStartedEvent[]>([]);
    const [finished, setFinished] = useState<Record<string, SubagentFinishedEvent>>({});
    const [failed, setFailed] = useState<Record<string, SubagentErrorEvent>>({});

    useEffect(() => {
        const subscription = agent.subscribe({
            onRunStartedEvent: () => {
                setStarted([]);
                setFinished({});
                setFailed({});
            },
            onSubagentStartedEvent: ({ event }) => setStarted((all) => [...all, event]),
            onSubagentFinishedEvent: ({ event }) =>
                setFinished((all) => ({ ...all, [event.subagentRunId]: event })),
            onSubagentErrorEvent: ({ event }) =>
                setFailed((all) => ({ ...all, [event.subagentRunId]: event })),
        });
        return () => subscription.unsubscribe();
    }, [agent]);

    const state = (agent.state ?? {}) as SharedState;
    const favorites = state.favorites ?? [];
    const location = state.location;

    return (
        <aside className="w-72 shrink-0 space-y-4 text-sm text-gray-300">
            <Section title="Sub-agents">
                {started.length === 0 ? (
                    <Muted>None called in this run.</Muted>
                ) : (
                    started.map((run) => {
                        const error = failed[run.subagentRunId];
                        const done = finished[run.subagentRunId];
                        const detail = error ? error.message : stringify(done?.result);
                        return (
                            <div
                                key={run.subagentRunId}
                                className="rounded-lg border border-[#2e2e2e] bg-[#171717]/80 p-2"
                            >
                                <div className="flex items-center gap-2">
                                    <span
                                        className={`inline-block w-2 h-2 rounded-full ${
                                            error
                                                ? "bg-red-500"
                                                : done
                                                  ? "bg-emerald-500"
                                                  : "bg-amber-500 animate-pulse"
                                        }`}
                                    />
                                    <span className="font-medium">{run.name}</span>
                                </div>
                                {run.description && (
                                    <p className="mt-1 text-xs text-gray-500 line-clamp-2">{run.description}</p>
                                )}
                                {detail && <p className="mt-1 text-xs text-gray-400 line-clamp-4">{detail}</p>}
                            </div>
                        );
                    })
                )}
            </Section>

            <Section title="Shared state">
                {location?.name && (
                    <p className="text-xs text-gray-400">
                        Last place: {[location.name, location.region, location.country].filter(Boolean).join(", ")}
                    </p>
                )}
                {favorites.length === 0 ? (
                    <Muted>No favorite cities yet. Ask the assistant to save one.</Muted>
                ) : (
                    <ul className="space-y-1">
                        {favorites.map((city) => (
                            <li key={city}>★ {city}</li>
                        ))}
                    </ul>
                )}
            </Section>
        </aside>
    );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <section className="space-y-2">
            <h2 className="text-xs uppercase tracking-wider text-gray-500 font-medium">{title}</h2>
            {children}
        </section>
    );
}

function Muted({ children }: { children: React.ReactNode }) {
    return <p className="text-xs text-gray-500">{children}</p>;
}

function stringify(value: unknown): string | undefined {
    if (value == null) return undefined;
    return typeof value === "string" ? value : JSON.stringify(value);
}
