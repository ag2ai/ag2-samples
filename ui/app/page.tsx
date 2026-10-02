"use client";

import {
    CopilotChat,
    useFrontendTool,
    useRenderTool,
} from "@copilotkit/react-core/v2";
import { z } from "zod";

// The tools take structured arguments the cards do not show, so the renderers accept any.
const anyArguments = z.looseObject({});

export default function Home() {
    useRenderTool({
        parameters: anyArguments,
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

    useRenderTool({
        parameters: anyArguments,
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

    useRenderTool({
        parameters: anyArguments,
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
        parameters: z.object({}),
        handler: async () => {
            // Report a refused or unavailable location as data, the way the backend tools
            // report a failed upstream call. Throwing here would fail the whole run, and the
            // agent could never reach its documented fallback of asking for a city name.
            try {
                const position = await getUserPosition();
                return {
                    latitude: position.latitude,
                    longitude: position.longitude,
                    accuracy: position.accuracy,
                };
            } catch (error) {
                return {
                    error:
                        error instanceof Error
                            ? error.message
                            : "Could not determine your location.",
                };
            }
        },
    });

    return (
        <main className="dark min-h-screen bg-[#0d0d0d]">
            <div className="relative h-screen py-10">
                <div className="relative h-full w-[50%] mx-auto flex flex-col">
                    <CopilotChat
                        agentId="agenticChatAgent"
                        className="h-full flex-1 min-h-0"
                        labels={{
                            modalHeaderTitle: "Weather Assistant",
                            welcomeMessageText:
                                "Hello! I'm a weather assistant and ready to help you with your weather questions.",
                        }}
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

/**
 * Tool results arrive as JSON on the AG-UI wire: the backend returns a dataclass and AG2
 * serialises it into the tool-result event's content.
 */
function parseToolResult<T>(result: unknown): T | null {
    let value = result;
    if (typeof value === "string") {
        try {
            value = JSON.parse(value);
        } catch {
            return null;
        }
    }
    // A scalar or an array is not a result object: fall through to the raw payload.
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
        return null;
    }
    return value as T;
}

function CurrentWeatherCard({ result }: { result: unknown }) {
    const parsed = parseToolResult<CurrentWeatherResult>(result);
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
    const parsed = parseToolResult<WeeklyForecastResult>(result);
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