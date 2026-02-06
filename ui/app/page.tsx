"use client";

import { useState } from "react";
import { useRenderToolCall, useFrontendTool } from "@copilotkit/react-core";
import {
    CopilotChat,
    CopilotKitCSSProperties,
    InputProps,
} from "@copilotkit/react-ui";

export default function Home() {
    useRenderToolCall({
        name: "get_coords_by_city",
        render: ({ status }) => {
            if (status !== "complete") {
                return (
                    <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm py-2">
                        <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
                        Getting city coordinates...
                    </div>
                );
            }

            return <></>;
        },
    });

    useRenderToolCall({
        name: "get_current_weather_by_coords",
        render: ({ status, result }) => {
            if (status !== "complete") {
                return (
                    <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm py-2">
                        <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
                        Getting current weather...
                    </div>
                );
            }

            if (status === "complete" && result != null) {
                return <CurrentWeatherCard result={result} />;
            }

            return <></>;
        },
    });

    useRenderToolCall({
        name: "get_weather_next_week",
        render: ({ status, result }) => {
            if (status !== "complete") {
                return (
                    <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm py-2">
                        <div className="w-4 h-4 border-2 border-gray-500 border-t-transparent rounded-full animate-spin" />
                        Getting weekly forecast...
                    </div>
                );
            }

            if (status === "complete" && result != null) {
                return <WeeklyForecastCard result={result} />;
            }

            return <></>;
        },
    });

    useFrontendTool({
        name: "getUserLocation",
        description:
            `Get the user's current geographic position (latitude and longitude)
      using the browser's Geolocation API. Call this when you need the user's location,
      for example to provide weather for their area. The user will be prompted to allow
      location access if not already granted.
      The user will be prompted to allow location access if not already granted.`,
        parameters: [],
        handler: async () => {
            const position = await getUserPosition();
            return {
                latitude: position.latitude,
                longitude: position.longitude,
                accuracy: position.accuracy,
            };
        },
    });

    return (
        <main className="dark min-h-screen bg-[#0d0d0d]">
            <div
                className="copilot-chat-dark relative h-screen py-10"
                style={
                    {
                        "--copilot-kit-background-color": "#0d0d0d",
                        "--copilot-kit-secondary-color": "#171717",
                        "--copilot-kit-secondary-contrast-color": "#ececec",
                        "--copilot-kit-separator-color": "#2e2e2e",
                        "--copilot-kit-input-background-color": "#2a2a2a",
                        "--copilot-kit-primary-color": "#2f2f2f",
                        "--copilot-kit-contrast-color": "#ececec",
                    } as CopilotKitCSSProperties
                }
            >
                <div className="relative h-full w-[50%] mx-auto flex flex-col">
                    <CopilotChat
                        className="h-full flex-1 min-h-0"
                        labels={{
                            title: "Weather Assistant",
                            initial:
                                "Hello! I'm a weather assistant and ready to help you with your weather questions.",
                        }}
                        Input={CustomInput}
                    />
                </div>
            </div>
        </main>
    );
}


function ToolCallCard({
    title,
    status,
    args,
    result,
}: {
    title: string;
    status: "running" | "complete";
    args?: Record<string, unknown>;
    result?: string;
}) {
    return (
        <div className="rounded-xl border border-[#2e2e2e] bg-[#171717]/80 overflow-hidden text-sm">
            <div className="flex items-center gap-2 px-3 py-2 border-b border-[#2e2e2e]">
                <span
                    className={`inline-block w-2 h-2 rounded-full shrink-0 ${status === "running"
                            ? "bg-amber-500 animate-pulse"
                            : "bg-emerald-500"
                        }`}
                />
                <span className="font-medium text-gray-300">{title}</span>
                {status === "running" && (
                    <span className="text-gray-500 text-xs">running…</span>
                )}
            </div>
            {args && Object.keys(args).length > 0 && (
                <div className="px-3 py-2 text-gray-400 font-mono text-xs">
                    {JSON.stringify(args)}
                </div>
            )}
            {result != null && result !== "" && (
                <pre className="px-3 py-2 text-gray-300 whitespace-pre-wrap break-words font-mono text-xs max-h-48 overflow-y-auto border-t border-[#2e2e2e]">
                    {result}
                </pre>
            )}
        </div>
    );
}

type CurrentWeatherResult = {
    error?: string;
    location?: string;
    conditions?: string;
    temperature?: string;
    feelsLike?: string;
    humidity?: string;
    wind?: string;
    precipitation?: string;
    dataTime?: string;
};

function normalizeCurrentWeatherResult(result: unknown): CurrentWeatherResult | null {
    if (typeof result === "string") {
        // Try JSON first
        try {
            return normalizeCurrentWeatherResult(JSON.parse(result));
        } catch {
            // Fall back to Python dict repr (single quotes)
            try {
                const jsonStr = result
                    .replace(/^"|"$/g, "")  // Remove outer quotes if present
                    .split(/(?<=\})\s*(?=\{)/)[0]  // Take first dict if duplicated
                    .replace(/'/g, '"')  // Convert single quotes to double quotes
                    .replace(/\bNone\b/g, "null")
                    .replace(/\bTrue\b/g, "true")
                    .replace(/\bFalse\b/g, "false");
                return normalizeCurrentWeatherResult(JSON.parse(jsonStr));
            } catch {
                return null;
            }
        }
    }

    if (!result || typeof result !== "object") {
        return null;
    }

    const data = result as Record<string, unknown>;
    const out: CurrentWeatherResult = {};
    if (typeof data.error === "string") {
        return { error: data.error };
    }

    if (typeof data.location === "string") out.location = data.location;
    if (typeof data.conditions === "string") out.conditions = data.conditions;
    if (typeof data.temperature === "string") out.temperature = data.temperature;
    if (typeof data.feelsLike === "string") out.feelsLike = data.feelsLike;
    if (typeof data.humidity === "string") out.humidity = data.humidity;
    if (typeof data.wind === "string") out.wind = data.wind;
    if (typeof data.precipitation === "string") out.precipitation = data.precipitation;
    if (typeof data.dataTime === "string") out.dataTime = data.dataTime;

    return Object.keys(out).length > 0 ? out : null;
}

function CurrentWeatherCard({ result }: { result: unknown }) {
    const parsed = normalizeCurrentWeatherResult(result);
    const isError = parsed?.error;

    if (isError) {
        return (
            <div className="rounded-xl border border-red-900/50 bg-red-950/20 overflow-hidden text-sm">
                <div className="flex items-center gap-2 px-3 py-2 border-b border-red-900/50">
                    <span className="inline-block w-2 h-2 rounded-full shrink-0 bg-red-500" />
                    <span className="font-medium text-red-300">Current weather</span>
                </div>
                <p className="px-3 py-2 text-red-200/90 text-xs">{parsed?.error}</p>
            </div>
        );
    }

    if (!parsed) {
        return (
            <div className="rounded-xl border border-[#2e2e2e] bg-[#171717]/80 overflow-hidden text-sm">
                <div className="flex items-center gap-2 px-3 py-2 border-b border-[#2e2e2e]">
                    <span className="inline-block w-2 h-2 rounded-full shrink-0 bg-emerald-500" />
                    <span className="font-medium text-gray-300">Current weather</span>
                </div>
                <pre className="px-3 py-2 text-gray-300 whitespace-pre-wrap break-words font-mono text-xs">
                    {JSON.stringify(result, null, 2)}
                </pre>
            </div>
        );
    }

    return (
        <div className="rounded-xl border border-[#2e2e2e] bg-[#171717]/90 overflow-hidden text-sm shadow-lg">
            <div className="px-4 py-3 border-b border-[#2e2e2e] bg-[#1a1a1a]/80">
                <p className="text-xs text-gray-500 uppercase tracking-wider font-medium">
                    Current weather
                </p>
                {parsed.location && (
                    <p className="text-gray-200 font-medium mt-0.5">{parsed.location}</p>
                )}
            </div>
            <div className="p-4 space-y-4">
                {(parsed.conditions ?? parsed.temperature) && (
                    <div className="flex items-baseline gap-3 flex-wrap">
                        {parsed.temperature && (
                            <span className="text-3xl font-light text-white tabular-nums">
                                {parsed.temperature}
                            </span>
                        )}
                        {parsed.conditions && (
                            <span className="text-gray-400">{parsed.conditions}</span>
                        )}
                    </div>
                )}
                {parsed.feelsLike && (
                    <p className="text-gray-400 text-xs">
                        Feels like {parsed.feelsLike}
                    </p>
                )}
                <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
                    {parsed.humidity && (
                        <div>
                            <span className="text-gray-500">Humidity</span>
                            <p className="text-gray-300">{parsed.humidity}</p>
                        </div>
                    )}
                    {parsed.wind && (
                        <div>
                            <span className="text-gray-500">Wind</span>
                            <p className="text-gray-300">{parsed.wind}</p>
                        </div>
                    )}
                    {parsed.precipitation != null && (
                        <div>
                            <span className="text-gray-500">Precipitation</span>
                            <p className="text-gray-300">{parsed.precipitation}</p>
                        </div>
                    )}
                </div>
                {parsed.dataTime && (
                    <p className="text-gray-500 text-xs pt-1 border-t border-[#2e2e2e]">
                        {parsed.dataTime}
                    </p>
                )}
            </div>
        </div>
    );
}

type WeeklyForecastDay = {
    date: string;
    conditions: string;
    tempMax: string;
    tempMin: string;
    precipitation: string;
    precipitationProbability: string;
};

type WeeklyForecastResult = {
    error?: string;
    location?: string;
    timezone?: string;
    days?: WeeklyForecastDay[];
};

/** Extract the first balanced {...} or [...] from a string (handles nested braces and quoted content). */
function extractFirstObjectString(str: string): string | null {
    const start = str.indexOf("{");
    if (start === -1) return null;
    let depth = 0;
    let i = start;
    let inString = false;
    let quoteChar: string | null = null;
    while (i < str.length) {
        if (inString) {
            if (str[i] === "\\") {
                i += 2;
                continue;
            }
            if (str[i] === quoteChar) {
                inString = false;
                quoteChar = null;
            }
            i++;
            continue;
        }
        if (str[i] === '"' || str[i] === "'") {
            inString = true;
            quoteChar = str[i];
            i++;
            continue;
        }
        if (str[i] === "{") depth++;
        else if (str[i] === "}") {
            depth--;
            if (depth === 0) return str.slice(start, i + 1);
        }
        i++;
    }
    return null;
}

function normalizeWeeklyForecastResult(result: unknown): WeeklyForecastResult | null {
    if (typeof result === "string") {
        let toParse = result.trim().replace(/^"|"$/g, "");
        const firstObj = extractFirstObjectString(toParse);
        if (firstObj) toParse = firstObj;
        try {
            return normalizeWeeklyForecastResult(JSON.parse(toParse));
        } catch {
            try {
                const jsonStr = toParse
                    .replace(/'/g, '"')
                    .replace(/\bNone\b/g, "null")
                    .replace(/\bTrue\b/g, "true")
                    .replace(/\bFalse\b/g, "false");
                return normalizeWeeklyForecastResult(JSON.parse(jsonStr));
            } catch {
                return null;
            }
        }
    }

    if (Array.isArray(result) && result.length > 0) {
        return normalizeWeeklyForecastResult(result[0]);
    }

    if (!result || typeof result !== "object") {
        return null;
    }

    const data = result as Record<string, unknown>;
    if (typeof data.error === "string") {
        return { error: data.error };
    }

    const out: WeeklyForecastResult = {};
    if (typeof data.location === "string") out.location = data.location;
    if (typeof data.timezone === "string") out.timezone = data.timezone;
    if (Array.isArray(data.days)) {
        out.days = data.days
            .filter((d): d is Record<string, unknown> => d != null && typeof d === "object")
            .map((d) => ({
                date: typeof d.date === "string" ? d.date : "",
                conditions: typeof d.conditions === "string" ? d.conditions : "",
                tempMax: typeof d.tempMax === "string" ? d.tempMax : "",
                tempMin: typeof d.tempMin === "string" ? d.tempMin : "",
                precipitation: typeof d.precipitation === "string" ? d.precipitation : "",
                precipitationProbability:
                    typeof d.precipitationProbability === "string" ? d.precipitationProbability : "",
            }));
    }

    return out.location != null || (out.days != null && out.days.length > 0) ? out : null;
}

function formatForecastDate(dateStr: string): string {
    if (!dateStr) return "";
    try {
        const d = new Date(dateStr);
        return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
    } catch {
        return dateStr;
    }
}

function WeeklyForecastCard({ result }: { result: unknown }) {
    const parsed = normalizeWeeklyForecastResult(result);
    const isError = parsed?.error;

    if (isError) {
        return (
            <div className="rounded-xl border border-red-900/50 bg-red-950/20 overflow-hidden text-sm">
                <div className="flex items-center gap-2 px-3 py-2 border-b border-red-900/50">
                    <span className="inline-block w-2 h-2 rounded-full shrink-0 bg-red-500" />
                    <span className="font-medium text-red-300">Weekly forecast</span>
                </div>
                <p className="px-3 py-2 text-red-200/90 text-xs">{parsed?.error}</p>
            </div>
        );
    }

    if (!parsed?.days?.length) {
        return (
            <div className="rounded-xl border border-[#2e2e2e] bg-[#171717]/80 overflow-hidden text-sm">
                <div className="flex items-center gap-2 px-3 py-2 border-b border-[#2e2e2e]">
                    <span className="inline-block w-2 h-2 rounded-full shrink-0 bg-emerald-500" />
                    <span className="font-medium text-gray-300">Weekly forecast</span>
                </div>
                <pre className="px-3 py-2 text-gray-300 whitespace-pre-wrap break-words font-mono text-xs">
                    {JSON.stringify(result, null, 2)}
                </pre>
            </div>
        );
    }

    return (
        <div className="rounded-xl border border-[#2e2e2e] bg-[#171717]/90 overflow-hidden text-sm shadow-lg">
            <div className="px-4 py-3 border-b border-[#2e2e2e] bg-[#1a1a1a]/80">
                <p className="text-xs text-gray-500 uppercase tracking-wider font-medium">
                    Weekly forecast
                </p>
                {parsed.location && (
                    <p className="text-gray-200 font-medium mt-0.5">{parsed.location}</p>
                )}
            </div>
            <div className="divide-y divide-[#2e2e2e]">
                {parsed.days.map((day, i) => (
                    <div
                        key={day.date || i}
                        className="px-4 py-3 flex items-center justify-between gap-4 flex-wrap"
                    >
                        <div className="min-w-0">
                            <p className="text-gray-200 font-medium">
                                {formatForecastDate(day.date) || day.date}
                            </p>
                            {day.conditions && (
                                <p className="text-gray-500 text-xs mt-0.5">{day.conditions}</p>
                            )}
                        </div>
                        <div className="flex items-center gap-4 shrink-0 text-right">
                            {(day.tempMax || day.tempMin) && (
                                <span className="text-gray-300 tabular-nums">
                                    {day.tempMin && <span>{day.tempMin}</span>}
                                    {day.tempMin && day.tempMax && (
                                        <span className="text-gray-500 mx-1">→</span>
                                    )}
                                    {day.tempMax && <span className="font-medium">{day.tempMax}</span>}
                                </span>
                            )}
                            {day.precipitationProbability && (
                                <span className="text-gray-500 text-xs">
                                    {day.precipitationProbability} precip
                                </span>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function CustomInput({
    inProgress,
    onSend,
    onStop,
    hideStopButton,
    chatReady,
}: InputProps) {
    const [input, setInput] = useState("");
    const isLlmGenerating = inProgress || !chatReady;

    const handleSend = async () => {
        const text = input.trim();
        if (!text || isLlmGenerating) return;
        setInput("");
        await onSend(text);
    };

    return (
        <div className="w-full sticky bottom-0 right-0 z-20 mt-6">
            {isLlmGenerating && <ThinkingBlock />}

            <div className="flex items-end">
                <div className="relative flex-1">
                    <textarea
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder={isLlmGenerating ? "Thinking..." : "Type a message..."}
                        disabled={isLlmGenerating}
                        rows={1}
                        className="w-full resize-none rounded-3xl max-h-[200px] overflow-y-auto px-4 py-4 text-md leading-6 focus:outline-none focus:ring-2 focus:ring-primary-500/20 bg-zinc-800 text-white disabled:opacity-50 disabled:cursor-not-allowed pr-12"
                    />

                    {isLlmGenerating && !hideStopButton && onStop ? (
                        <button
                            onClick={onStop}
                            className="absolute right-2 bottom-4 p-2 bg-gray-500 text-white rounded-full hover:bg-gray-600 transition-colors"
                            title="Stop generating"
                        >
                            ■
                        </button>
                    ) : (
                        <button
                            onClick={handleSend}
                            disabled={!input.trim()}
                            className="absolute right-2 bottom-4 p-2 bg-primary-500 text-white rounded-full hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            title="Send message"
                        >
                            ➤
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}

function ThinkingBlock() {
    return (
        <div className="mx-auto flex items-center gap-2 px-4 py-2.5 text-sm text-gray-400 w-fit shrink-0 mb-2">
            <span>Thinking</span>
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-500 animate-pulse" />
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-500 animate-pulse [animation-delay:0.2s]" />
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-gray-500 animate-pulse [animation-delay:0.4s]" />
        </div>
    );
}

function getUserPosition(): Promise<{
    latitude: number;
    longitude: number;
    accuracy?: number;
}> {
    return new Promise((resolve, reject) => {
        if (!navigator?.geolocation) {
            reject(new Error("Geolocation is not supported by this browser."));
            return;
        }

        const options: PositionOptions = {
            enableHighAccuracy: false,
            timeout: 15000,
            maximumAge: 60000, // 1 min cache
        };

        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                });
            },

            (error: GeolocationPositionError) => {
                const message =
                    error.code === 1
                        ? "Location access was denied. Please allow location in your browser or system settings and try again."
                        : error.code === 2
                            ? "Location could not be determined. Please ensure location services are enabled in your system settings, then try again. If you're on a desktop, you may need to allow the site to use your location."
                            : "Location request timed out. Please check your connection and try again.";
                reject(new Error(message));
            },

            options
        );
    });
}