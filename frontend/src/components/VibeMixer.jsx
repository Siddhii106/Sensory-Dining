import { useReducer } from "react";
import {
    Sofa,
    UtensilsCrossed,
    Laptop,
    Moon,
    Sun,
    Monitor,
    Music,
    Waves,
    Loader2,
} from "lucide-react";

const ROOM_OPTIONS = [
    { value: "couch", label: "Couch", Icon: Sofa },
    { value: "table", label: "Table", Icon: UtensilsCrossed },
    { value: "desk", label: "Desk", Icon: Laptop },
];

const LIGHTING_OPTIONS = [
    { value: "dim", label: "Dim", Icon: Moon },
    { value: "bright", label: "Bright", Icon: Sun },
    { value: "screen_glow", label: "Screen Glow", Icon: Monitor },    
];

const DURATION_OPTIONS = [
    { value: 15, label: "15 min" },
    { value: 30, label: "30 min" },
    { value: 60, label: "60 min" },
];

const AUDIO_OPTIONS = [
    { value: "playlist", label: "Playlist", Icon: Music },
    { value: "soundscape", label: "Soundscape", Icon: Waves },    
];

const INITIAL_STATE = {
    roomType: "couch",
    lighting: "dim",
    moodScore: 50,
    durationMinutes: 30,
    audioMode: "playlist",
};

function mixerReducer(state, action) {
    switch (action.type) {
        case "set":
            return {...state, [action.key]: action.value };
        default:
            return state;
    }
}

function moodLabel(score) {
    if (score < 20) return "Running on empty";
    if (score < 40) return "Low battery";
    if (score < 60) return "Steady";
    if (score < 80) return "Charging up";
    return "Full charge";
}

function ChoiceGroup({ legend, options, value, onChange, columns = 3 }) {
    return (
        <fieldset>
            <legend className="mb-3 text-[11px] uppercase tracking-[0.25em] text-slate-400">
                {legend}
            </legend>
            <div
                role="radiogroup"
                aria-label={legend}
                className={`grid gap-3 ${columns === 2 ? "grid-cols-2" : "grid-cols-3"}`}
            >
                {options.map(({ value: optionValue, label, Icon }) => {
                    const active = optionValue === value;
                    return (
                        <button
                            key={optionValue}
                            type="button"
                            role="radio"
                            aria-checked={active}
                            onClick={() => onChange(optionValue)}
                            className={[
                                "group flex flex-col items-center justify-center gap-2 rounded-xl border px-3 py-4",
                                "text-sm tracking-wide",
                                "motion-safe:transition-all motion-safe:duration-300 motion-safe:ease-out",
                                "motion-safe:active:scale-[0.97]",
                                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold/60",
                                active
                                ? "border-gold bg-gold/10 text-gold-soft shadow-glow"
                                : "border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-600 hover:text-slate-200",
                            ].join(" ")}
                        >
                            {Icon && (
                                <Icon
                                    aria-hidden="true"
                                    strokeWidth={1.5}
                                    className="h-5 w-5 motion-safe:transition-transform motion-safe:duration-300 motion-safe:group-hover:-translate-y-0.5"
                                />
                            )}
                            <span>{label}</span>
                        </button>
                    );
                })}    
            </div>
        </fieldset>
    );
}

function MoodSlider({ value, onChange }) {
    const label = moodLabel(value);
    return (
        <div className="space-y-4">
            <div className="flex items-baseline justify-between">
                <label htmlFor="mood-slider" className="text-[11px] uppercase tracking-[0.25em] text-slate-400">
                    Mood
                </label>
                <span className="text-sm text-gold-soft transition-opacity duration-300">{label}</span>
            </div>
            <input
                id="mood-slider"
                type="range"
                min={0}
                max={100}
                step={1}
                value={value}
                onChange={(event) => onChange(Number(event.target.value))}
                aria-valuetext={label}
                className="mixer-slider w-full"
                style={{  "--fill": `${value}%` }}
            />
            <div className="flex justify-between text-[11px] uppercase tracking-widest text-slate-500">
                <span>Low Battery</span>
                <span>Full Charge</span>
            </div>
        </div>
    );
}

export default function VibeMixer({ onSubmit, isSubmitting = false, className = "" }) {
    const [state, dispatch] = useReducer(mixerReducer, INITIAL_STATE);

    const setField = (key) => (value) => dispatch({ type: "set", key, value });

    const handleSubmit = (event) => {
        event.preventDefault();
        onSubmit({
            room_type: state.roomType,
            lighting: state.lighting,
            mood_score: state.moodScore,
            duration_minutes: state.durationMinutes,
            audio_mode: state.audioMode,
        });
    };

    return (
        <section
            aria-labelledby="vibe-mixer-title"
            className={`mx-auto w-full max-w-md rounded-3xl border border-white/5 bg-gradient-to-b from-[#14161D] to-obsidian p-8 shadow-2xl ${className}`}
        >
            <form onSubmit={handleSubmit} className="space-y-8">
                <header>
                    <p className="text-[11px] uppercase tracking-[0.35em] text-gold/80">Ambience Engine</p>
                    <h2 id="vibe-mixer-title" className="mt-2 text-3xl font-semibold text-slate-100">
                        Vibe Mixer
                    </h2>
                    <p className="mt-2 text-sm text-slate-400">
                        Set the room and your energy. We will score the soundtrack to your plate.
                    </p>
                </header>

                <ChoiceGroup
                    legend="Room"
                    options={ROOM_OPTIONS}
                    value={state.roomType}
                    onChange={setField("roomType")}
                />

                <ChoiceGroup
                    legend="Lighting"
                    options={LIGHTING_OPTIONS}
                    value={state.lighting}
                    onChange={setField("lighting")}
                />

                <MoodSlider value={state.moodScore} onChange={setField("moodScore")} />

                <ChoiceGroup
                    legend="Meal length"
                    options={DURATION_OPTIONS}
                    value={state.durationMinutes}
                    onChange={setField("durationMinutes")}
                />

                <ChoiceGroup
                    legend="Audio"
                    options={AUDIO_OPTIONS}
                    value={state.audioMode}
                    onChange={setField("audioMode")}
                    columns={2}
                />

                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-gold px-4 py-3.5 text-sm font-semibold tracking-wide text-obsidian shadow-glow motion-safe:transition-all motion-safe:duration-300 hover:bg-gold-soft motion-safe:active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {isSubmitting ? (
                        <>
                            <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden="true" />
                            Composing
                        </>
                    ) : (
                        "Start Ambience"
                    )}
                </button>
            </form>
        </section>
    );
}