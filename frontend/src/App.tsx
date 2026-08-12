import { useState, useEffect, useCallback } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface User {
    id: number;
    name: string;
    account_number: string;
    role: string;
    pin_code: string;
}

interface Item {
    id?: number;
    name: string;
    price: number;
}

interface Transaction {
    id: number;
    name: string;
    description?: string;
    shop_name: string;
    owner_id: number;
    event_id?: number;
    participants: User[];
    items: Item[];
}

interface Event {
    id: number;
    name: string;
    description?: string;
    owner_id: number;
    transactions: Transaction[];
}

type View = "login" | "register" | "events" | "transactions" | "balances";

// ─── API ─────────────────────────────────────────────────────────────────────

const BASE = "http://localhost:8000";

async function api<T>(
    path: string,
    options: RequestInit = {}
): Promise<T> {
    const res = await fetch(`${BASE}${path}`, {
        credentials: "include",
        headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(err.detail ?? "Request failed");
    }
    return res.json();
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function totalOf(t: Transaction) {
    return t.items.reduce((s, i) => s + i.price, 0);
}

function perPersonOf(t: Transaction) {
    const n = t.participants.length;
    return n > 0 ? totalOf(t) / n : totalOf(t);
}

/** Who owes whom, simplified */
function computeBalances(transactions: Transaction[], users: User[]) {
    const net: Record<number, number> = {};
    users.forEach((u) => (net[u.id] = 0));

    for (const t of transactions) {
        const total = totalOf(t);
        const n = t.participants.length;
        if (n === 0) continue;
        const share = total / n;
        // payer (owner) is owed the total
        net[t.owner_id] = (net[t.owner_id] ?? 0) + total;
        // each participant owes their share
        for (const p of t.participants) {
            net[p.id] = (net[p.id] ?? 0) - share;
        }
    }
    return net;
}

function userName(id: number, users: User[]) {
    return users.find((u) => u.id === id)?.name ?? `#${id}`;
}

// ─── Tiny UI atoms ────────────────────────────────────────────────────────────

function Badge({ children, color = "slate" }: { children: React.ReactNode; color?: string }) {
    const map: Record<string, string> = {
        slate: "bg-slate-100 text-slate-700",
        green: "bg-emerald-100 text-emerald-700",
        red: "bg-red-100 text-red-700",
        blue: "bg-blue-100 text-blue-700",
        amber: "bg-amber-100 text-amber-800",
    };
    return (
        <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${map[color] ?? map.slate}`}>
            {children}
        </span>
    );
}

function Spinner() {
    return (
        <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        </div>
    );
}

function ErrorBox({ msg, onClose }: { msg: string; onClose: () => void }) {
    return (
        <div className="flex items-start gap-3 bg-red-50 border border-red-200 text-red-800 rounded-lg px-4 py-3 text-sm">
            <span className="mt-0.5">⚠</span>
            <span className="flex-1">{msg}</span>
            <button onClick={onClose} className="text-red-400 hover:text-red-600 font-bold leading-none">×</button>
        </div>
    );
}

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] flex flex-col">
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
                    <h3 className="font-semibold text-slate-800">{title}</h3>
                    <button onClick={onClose} className="w-8 h-8 flex items-center justify-center rounded-full hover:bg-slate-100 text-slate-500">×</button>
                </div>
                <div className="overflow-y-auto px-6 py-4">{children}</div>
            </div>
        </div>
    );
}

function Input({ label, ...props }: { label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
    return (
        <label className="flex flex-col gap-1">
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">{label}</span>
            <input
                className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
                {...props}
            />
        </label>
    );
}

function Btn({
    children,
    variant = "primary",
    size = "md",
    ...props
}: {
    children: React.ReactNode;
    variant?: "primary" | "ghost" | "danger" | "outline";
    size?: "sm" | "md";
} & React.ButtonHTMLAttributes<HTMLButtonElement>) {
    const base = "rounded-lg font-medium transition-all focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-50";
    const variants = {
        primary: "bg-indigo-600 hover:bg-indigo-700 text-white focus:ring-indigo-400",
        ghost: "bg-transparent hover:bg-slate-100 text-slate-700 focus:ring-slate-300",
        danger: "bg-red-500 hover:bg-red-600 text-white focus:ring-red-400",
        outline: "border border-slate-200 hover:bg-slate-50 text-slate-700 focus:ring-slate-300",
    };
    const sizes = { sm: "px-3 py-1.5 text-xs", md: "px-4 py-2 text-sm" };
    return (
        <button className={`${base} ${variants[variant]} ${sizes[size]}`} {...props}>
            {children}
        </button>
    );
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

function LoginForm({ onSuccess, goRegister }: { onSuccess: (u: User) => void; goRegister: () => void }) {
    const [name, setName] = useState("");
    const [pin, setPin] = useState("");
    const [err, setErr] = useState("");
    const [loading, setLoading] = useState(false);

    async function submit(e: React.FormEvent) {
        e.preventDefault();
        setErr("");
        setLoading(true);
        try {
            const user = await api<User>("/login", {
                method: "POST",
                body: JSON.stringify({ name, pin_code: pin }),
            });
            onSuccess(user);
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-slate-100 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-8">
                <div className="text-center mb-8">
                    <div className="text-4xl mb-3">💸</div>
                    <h1 className="text-2xl font-bold text-slate-900">Money Manager</h1>
                    <p className="text-slate-500 text-sm mt-1">Track expenses with friends</p>
                </div>
                <form onSubmit={submit} className="flex flex-col gap-4">
                    {err && <ErrorBox msg={err} onClose={() => setErr("")} />}
                    <Input label="Name" value={name} onChange={e => setName(e.target.value)} required autoFocus />
                    <Input label="PIN (4 digits)" type="password" inputMode="numeric" maxLength={4} value={pin} onChange={e => setPin(e.target.value)} required />
                    <Btn type="submit" disabled={loading}>{loading ? "Signing in…" : "Sign in"}</Btn>
                </form>
                <p className="text-center text-sm text-slate-500 mt-6">
                    No account?{" "}
                    <button onClick={goRegister} className="text-indigo-600 font-medium hover:underline">Register</button>
                </p>
            </div>
        </div>
    );
}

function RegisterForm({ onSuccess, goLogin }: { onSuccess: (u: User) => void; goLogin: () => void }) {
    const [name, setName] = useState("");
    const [pin, setPin] = useState("");
    const [account, setAccount] = useState("");
    const [err, setErr] = useState("");
    const [loading, setLoading] = useState(false);

    async function submit(e: React.FormEvent) {
        e.preventDefault();
        setErr("");
        setLoading(true);
        try {
            const user = await api<User>("/register", {
                method: "POST",
                body: JSON.stringify({ name, pin_code: pin, account_number: account }),
            });
            onSuccess(user);
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-slate-100 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-sm p-8">
                <div className="text-center mb-8">
                    <div className="text-4xl mb-3">💸</div>
                    <h1 className="text-2xl font-bold text-slate-900">Create account</h1>
                    <p className="text-slate-500 text-sm mt-1">Set up your Money Manager profile</p>
                </div>
                <form onSubmit={submit} className="flex flex-col gap-4">
                    {err && <ErrorBox msg={err} onClose={() => setErr("")} />}
                    <Input label="Name" value={name} onChange={e => setName(e.target.value)} required autoFocus />
                    <Input label="Account number (optional)" value={account} onChange={e => setAccount(e.target.value)} placeholder="IBAN or other" />
                    <Input label="PIN (4 digits)" type="password" inputMode="numeric" maxLength={4} value={pin} onChange={e => setPin(e.target.value)} required />
                    <Btn type="submit" disabled={loading}>{loading ? "Creating…" : "Create account"}</Btn>
                </form>
                <p className="text-center text-sm text-slate-500 mt-6">
                    Already have one?{" "}
                    <button onClick={goLogin} className="text-indigo-600 font-medium hover:underline">Sign in</button>
                </p>
            </div>
        </div>
    );
}

// ─── Event forms ──────────────────────────────────────────────────────────────

function EventFormModal({
    initial,
    onSave,
    onClose,
}: {
    initial?: Event;
    onSave: (name: string, description: string) => Promise<void>;
    onClose: () => void;
}) {
    const [name, setName] = useState(initial?.name ?? "");
    const [desc, setDesc] = useState(initial?.description ?? "");
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");

    async function submit(e: React.FormEvent) {
        e.preventDefault();
        setErr("");
        setLoading(true);
        try {
            await onSave(name, desc);
            onClose();
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <Modal title={initial ? "Edit event" : "New event"} onClose={onClose}>
            <form onSubmit={submit} className="flex flex-col gap-4">
                {err && <ErrorBox msg={err} onClose={() => setErr("")} />}
                <Input label="Event name" value={name} onChange={e => setName(e.target.value)} required autoFocus placeholder="Summer trip to Bali" />
                <label className="flex flex-col gap-1">
                    <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Description</span>
                    <textarea
                        className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
                        rows={3}
                        value={desc}
                        onChange={e => setDesc(e.target.value)}
                        placeholder="Optional notes…"
                    />
                </label>
                <div className="flex justify-end gap-2 pt-2">
                    <Btn type="button" variant="ghost" onClick={onClose}>Cancel</Btn>
                    <Btn type="submit" disabled={loading}>{loading ? "Saving…" : "Save event"}</Btn>
                </div>
            </form>
        </Modal>
    );
}

// ─── Transaction form ─────────────────────────────────────────────────────────

function TransactionFormModal({
    initial,
    events,
    allUsers,
    currentUserId,
    onSave,
    onClose,
}: {
    initial?: Transaction;
    events: Event[];
    allUsers: User[];
    currentUserId: number;
    onSave: (data: any) => Promise<void>;
    onClose: () => void;
}) {
    const [name, setName] = useState(initial?.name ?? "");
    const [desc, setDesc] = useState(initial?.description ?? "");
    const [shop, setShop] = useState(initial?.shop_name ?? "");
    const [eventId, setEventId] = useState<number | "">(initial?.event_id ?? (events[0]?.id ?? ""));
    const [participants, setParticipants] = useState<number[]>(
        initial ? initial.participants.map(p => p.id) : [currentUserId]
    );
    const [items, setItems] = useState<{ name: string; price: string }[]>(
        initial ? initial.items.map(i => ({ name: i.name, price: String(i.price) })) : [{ name: "", price: "" }]
    );
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");

    function toggleParticipant(id: number) {
        setParticipants(prev =>
            prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
        );
    }

    function updateItem(idx: number, field: "name" | "price", val: string) {
        setItems(prev => prev.map((it, i) => i === idx ? { ...it, [field]: val } : it));
    }

    function addItem() { setItems(prev => [...prev, { name: "", price: "" }]); }
    function removeItem(idx: number) { setItems(prev => prev.filter((_, i) => i !== idx)); }

    const total = items.reduce((s, i) => s + (parseFloat(i.price) || 0), 0);
    const perPerson = participants.length > 0 ? total / participants.length : total;

    async function submit(e: React.FormEvent) {
        e.preventDefault();
        setErr("");
        setLoading(true);
        try {
            await onSave({
                name,
                description: desc || undefined,
                shop_name: shop,
                event_id: eventId || undefined,
                owner_id: currentUserId,
                participants,
                items: items.filter(i => i.name).map(i => ({ name: i.name, price: parseFloat(i.price) || 0 })),
            });
            onClose();
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setLoading(false);
        }
    }

    return (
        <Modal title={initial ? "Edit transaction" : "New transaction"} onClose={onClose}>
            <form onSubmit={submit} className="flex flex-col gap-5">
                {err && <ErrorBox msg={err} onClose={() => setErr("")} />}

                <div className="grid grid-cols-2 gap-3">
                    <div className="col-span-2">
                        <Input label="Transaction name" value={name} onChange={e => setName(e.target.value)} required placeholder="Dinner at the beach" />
                    </div>
                    <Input label="Shop / vendor" value={shop} onChange={e => setShop(e.target.value)} required placeholder="Sunset Restaurant" />
                    <label className="flex flex-col gap-1">
                        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Event</span>
                        <select
                            className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 bg-white"
                            value={eventId}
                            onChange={e => setEventId(Number(e.target.value))}
                        >
                            <option value="">— no event —</option>
                            {events.map(ev => <option key={ev.id} value={ev.id}>{ev.name}</option>)}
                        </select>
                    </label>
                    <div className="col-span-2">
                        <label className="flex flex-col gap-1">
                            <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Description</span>
                            <textarea
                                className="border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
                                rows={2}
                                value={desc}
                                onChange={e => setDesc(e.target.value)}
                                placeholder="Optional notes…"
                            />
                        </label>
                    </div>
                </div>

                {/* Items */}
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-medium text-slate-500 uppercase tracking-wide">Items</span>
                        <Btn type="button" variant="outline" size="sm" onClick={addItem}>+ Add item</Btn>
                    </div>
                    <div className="flex flex-col gap-2">
                        {items.map((item, idx) => (
                            <div key={idx} className="flex gap-2 items-center">
                                <input
                                    className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                                    placeholder="Item name"
                                    value={item.name}
                                    onChange={e => updateItem(idx, "name", e.target.value)}
                                />
                                <input
                                    className="w-24 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
                                    placeholder="Price"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={item.price}
                                    onChange={e => updateItem(idx, "price", e.target.value)}
                                />
                                {items.length > 1 && (
                                    <button type="button" onClick={() => removeItem(idx)} className="text-slate-400 hover:text-red-500 px-1">×</button>
                                )}
                            </div>
                        ))}
                    </div>
                    {total > 0 && (
                        <div className="mt-2 flex gap-4 text-xs text-slate-500">
                            <span>Total: <strong className="text-slate-800">{total.toFixed(2)}</strong></span>
                            {participants.length > 0 && (
                                <span>Per person: <strong className="text-slate-800">{perPerson.toFixed(2)}</strong></span>
                            )}
                        </div>
                    )}
                </div>

                {/* Participants */}
                <div>
                    <span className="text-xs font-medium text-slate-500 uppercase tracking-wide block mb-2">Participants</span>
                    <div className="flex flex-wrap gap-2">
                        {allUsers.map(u => (
                            <button
                                key={u.id}
                                type="button"
                                onClick={() => toggleParticipant(u.id)}
                                className={`px-3 py-1.5 rounded-full text-sm border transition-all ${participants.includes(u.id)
                                    ? "bg-indigo-600 text-white border-indigo-600"
                                    : "bg-white text-slate-600 border-slate-200 hover:border-indigo-300"
                                    }`}
                            >
                                {u.name}
                                {u.id === currentUserId && " (you)"}
                            </button>
                        ))}
                    </div>
                    {participants.length === 0 && (
                        <p className="text-xs text-red-500 mt-1">Select at least one participant.</p>
                    )}
                </div>

                <div className="flex justify-end gap-2 pt-2">
                    <Btn type="button" variant="ghost" onClick={onClose}>Cancel</Btn>
                    <Btn type="submit" disabled={loading || participants.length === 0}>
                        {loading ? "Saving…" : "Save transaction"}
                    </Btn>
                </div>
            </form>
        </Modal>
    );
}

// ─── Events view ──────────────────────────────────────────────────────────────

function EventsView({ me, allUsers }: { me: User; allUsers: User[] }) {
    const [events, setEvents] = useState<Event[]>([]);
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState("");
    const [showForm, setShowForm] = useState(false);
    const [editing, setEditing] = useState<Event | null>(null);
    const [expanded, setExpanded] = useState<number | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const data = await api<Event[]>("/events");
            setEvents(data);
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    async function createEvent(name: string, description: string) {
        await api("/events", { method: "POST", body: JSON.stringify({ name, description }) });
        await load();
    }

    async function editEvent(event: Event, name: string, description: string) {
        await api(`/events/${event.id}`, { method: "PUT", body: JSON.stringify({ name, description }) });
        await load();
    }

    async function deleteEvent(id: number) {
        if (!confirm("Delete this event and all its transactions?")) return;
        await api(`/events/${id}`, { method: "DELETE" });
        await load();
    }

    return (
        <div className="max-w-2xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-bold text-slate-900">Your events</h2>
                    <p className="text-sm text-slate-500 mt-0.5">Group your transactions into trips or occasions</p>
                </div>
                <Btn onClick={() => setShowForm(true)}>+ New event</Btn>
            </div>

            {err && <ErrorBox msg={err} onClose={() => setErr("")} />}
            {loading ? <Spinner /> : (
                events.length === 0 ? (
                    <div className="text-center py-16 text-slate-400">
                        <div className="text-5xl mb-3">🗓</div>
                        <p className="font-medium">No events yet</p>
                        <p className="text-sm mt-1">Create one to start grouping your expenses</p>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {events.map(ev => {
                            const txTotal = ev.transactions.reduce((s, t) => s + totalOf(t), 0);
                            const isOpen = expanded === ev.id;
                            return (
                                <div key={ev.id} className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden">
                                    <button
                                        className="w-full flex items-center justify-between px-5 py-4 hover:bg-slate-50 transition-colors text-left"
                                        onClick={() => setExpanded(isOpen ? null : ev.id)}
                                    >
                                        <div>
                                            <div className="font-semibold text-slate-900">{ev.name}</div>
                                            {ev.description && <div className="text-sm text-slate-500 mt-0.5">{ev.description}</div>}
                                        </div>
                                        <div className="flex items-center gap-3">
                                            <div className="text-right">
                                                <div className="text-sm font-bold text-indigo-600">{txTotal.toFixed(2)}</div>
                                                <div className="text-xs text-slate-400">{ev.transactions.length} tx</div>
                                            </div>
                                            <span className="text-slate-400 text-sm">{isOpen ? "▲" : "▼"}</span>
                                        </div>
                                    </button>

                                    {isOpen && (
                                        <div className="px-5 pb-4 border-t border-slate-100 pt-3">
                                            <div className="flex gap-2 mb-3">
                                                <Btn size="sm" variant="outline" onClick={() => setEditing(ev)}>Edit</Btn>
                                                <Btn size="sm" variant="danger" onClick={() => deleteEvent(ev.id)}>Delete</Btn>
                                            </div>
                                            {ev.transactions.length === 0 ? (
                                                <p className="text-sm text-slate-400">No transactions in this event.</p>
                                            ) : (
                                                <div className="flex flex-col gap-2">
                                                    {ev.transactions.map(t => (
                                                        <div key={t.id} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2 text-sm">
                                                            <div>
                                                                <span className="font-medium text-slate-800">{t.name}</span>
                                                                <span className="text-slate-400 ml-2 text-xs">@ {t.shop_name}</span>
                                                            </div>
                                                            <span className="font-medium text-slate-700">{totalOf(t).toFixed(2)}</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )
            )}

            {showForm && (
                <EventFormModal onSave={createEvent} onClose={() => setShowForm(false)} />
            )}
            {editing && (
                <EventFormModal
                    initial={editing}
                    onSave={(n, d) => editEvent(editing, n, d)}
                    onClose={() => setEditing(null)}
                />
            )}
        </div>
    );
}

// ─── Transactions view ────────────────────────────────────────────────────────

function TransactionsView({ me, allUsers }: { me: User; allUsers: User[] }) {
    const [txns, setTxns] = useState<Transaction[]>([]);
    const [events, setEvents] = useState<Event[]>([]);
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState("");
    const [showForm, setShowForm] = useState(false);
    const [editing, setEditing] = useState<Transaction | null>(null);

    const load = useCallback(async () => {
        setLoading(true);
        try {
            const [t, e] = await Promise.all([
                api<Transaction[]>("/transactions"),
                api<Event[]>("/events"),
            ]);
            setTxns(t);
            setEvents(e);
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    async function createTx(data: any) {
        await api("/transactions", { method: "POST", body: JSON.stringify(data) });
        await load();
    }

    async function editTx(id: number, data: any) {
        await api(`/transactions/${id}`, { method: "PUT", body: JSON.stringify(data) });
        await load();
    }

    async function deleteTx(id: number) {
        if (!confirm("Delete this transaction?")) return;
        await api(`/transactions/${id}`, { method: "DELETE" });
        await load();
    }

    return (
        <div className="max-w-2xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h2 className="text-xl font-bold text-slate-900">Your transactions</h2>
                    <p className="text-sm text-slate-500 mt-0.5">All purchases you recorded</p>
                </div>
                <Btn onClick={() => setShowForm(true)}>+ New transaction</Btn>
            </div>

            {err && <ErrorBox msg={err} onClose={() => setErr("")} />}
            {loading ? <Spinner /> : (
                txns.length === 0 ? (
                    <div className="text-center py-16 text-slate-400">
                        <div className="text-5xl mb-3">🧾</div>
                        <p className="font-medium">No transactions yet</p>
                        <p className="text-sm mt-1">Add one to start splitting costs</p>
                    </div>
                ) : (
                    <div className="flex flex-col gap-3">
                        {txns.map(t => {
                            const total = totalOf(t);
                            const per = perPersonOf(t);
                            const ev = events.find(e => e.id === t.event_id);
                            return (
                                <div key={t.id} className="bg-white rounded-xl border border-slate-100 shadow-sm p-5">
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="min-w-0">
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="font-semibold text-slate-900">{t.name}</span>
                                                {ev && <Badge color="blue">{ev.name}</Badge>}
                                            </div>
                                            <div className="text-sm text-slate-500 mt-0.5">@ {t.shop_name}</div>
                                            {t.description && <div className="text-sm text-slate-400 mt-1">{t.description}</div>}
                                        </div>
                                        <div className="text-right shrink-0">
                                            <div className="text-lg font-bold text-slate-900">{total.toFixed(2)}</div>
                                            {t.participants.length > 1 && (
                                                <div className="text-xs text-slate-400">{per.toFixed(2)} / person</div>
                                            )}
                                        </div>
                                    </div>

                                    <div className="mt-3 border-t border-slate-100 pt-3">
                                        <div className="flex flex-wrap gap-1 mb-2">
                                            {t.items.map((item, idx) => (
                                                <span key={idx} className="text-xs bg-slate-100 text-slate-600 rounded px-2 py-0.5">
                                                    {item.name} — {(item.price ?? 0).toFixed(2)}
                                                </span>
                                            ))}
                                        </div>
                                        <div className="flex items-center justify-between">
                                            <div className="flex flex-wrap gap-1">
                                                {t.participants.map(p => (
                                                    <Badge key={p.id} color={p.id === me.id ? "green" : "slate"}>
                                                        {p.name}{p.id === me.id ? " (you)" : ""}
                                                    </Badge>
                                                ))}
                                            </div>
                                            <div className="flex gap-2">
                                                <Btn size="sm" variant="outline" onClick={() => setEditing(t)}>Edit</Btn>
                                                <Btn size="sm" variant="danger" onClick={() => deleteTx(t.id)}>Delete</Btn>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )
            )}

            {(showForm || editing) && (
                <TransactionFormModal
                    initial={editing ?? undefined}
                    events={events}
                    allUsers={allUsers}
                    currentUserId={me.id}
                    onSave={editing ? (d) => editTx(editing.id, d) : createTx}
                    onClose={() => { setShowForm(false); setEditing(null); }}
                />
            )}
        </div>
    );
}

// ─── Balances view ────────────────────────────────────────────────────────────

function BalancesView({ me, allUsers }: { me: User; allUsers: User[] }) {
    const [txns, setTxns] = useState<Transaction[]>([]);
    const [loading, setLoading] = useState(true);
    const [err, setErr] = useState("");

    useEffect(() => {
        api<Transaction[]>("/transactions")
            .then(setTxns)
            .catch(e => setErr(e.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <Spinner />;

    const net = computeBalances(txns, allUsers);

    // Generate settlement suggestions
    const debtors = Object.entries(net)
        .filter(([, v]) => v < -0.005)
        .map(([id, v]) => ({ id: Number(id), amount: -v }))
        .sort((a, b) => b.amount - a.amount);

    const creditors = Object.entries(net)
        .filter(([, v]) => v > 0.005)
        .map(([id, v]) => ({ id: Number(id), amount: v }))
        .sort((a, b) => b.amount - a.amount);

    // Simple greedy settlement
    const settlements: { from: number; to: number; amount: number }[] = [];
    const d = debtors.map(x => ({ ...x }));
    const c = creditors.map(x => ({ ...x }));
    let di = 0, ci = 0;
    while (di < d.length && ci < c.length) {
        const pay = Math.min(d[di].amount, c[ci].amount);
        settlements.push({ from: d[di].id, to: c[ci].id, amount: pay });
        d[di].amount -= pay;
        c[ci].amount -= pay;
        if (d[di].amount < 0.005) di++;
        if (c[ci].amount < 0.005) ci++;
    }

    const usersWithBalance = allUsers.filter(u => Math.abs(net[u.id] ?? 0) > 0.005);

    return (
        <div className="max-w-2xl mx-auto">
            <div className="mb-6">
                <h2 className="text-xl font-bold text-slate-900">Balances</h2>
                <p className="text-sm text-slate-500 mt-0.5">Who paid and who still owes</p>
            </div>

            {err && <ErrorBox msg={err} onClose={() => setErr("")} />}

            {usersWithBalance.length === 0 ? (
                <div className="text-center py-16 text-slate-400">
                    <div className="text-5xl mb-3">✅</div>
                    <p className="font-medium">All settled up!</p>
                    <p className="text-sm mt-1">No outstanding balances.</p>
                </div>
            ) : (
                <>
                    <div className="bg-white rounded-xl border border-slate-100 shadow-sm divide-y divide-slate-100 mb-6">
                        {usersWithBalance.map(u => {
                            const bal = net[u.id] ?? 0;
                            return (
                                <div key={u.id} className="flex items-center justify-between px-5 py-3">
                                    <div className="flex items-center gap-3">
                                        <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold ${u.id === me.id ? "bg-indigo-100 text-indigo-700" : "bg-slate-100 text-slate-600"
                                            }`}>
                                            {u.name[0].toUpperCase()}
                                        </div>
                                        <div>
                                            <div className="font-medium text-slate-900">{u.name}{u.id === me.id ? " (you)" : ""}</div>
                                            {u.account_number && <div className="text-xs text-slate-400">{u.account_number}</div>}
                                        </div>
                                    </div>
                                    <div className={`font-bold text-sm ${bal > 0 ? "text-emerald-600" : "text-red-500"}`}>
                                        {bal > 0 ? "+" : ""}{bal.toFixed(2)}
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    {settlements.length > 0 && (
                        <div>
                            <h3 className="text-sm font-semibold text-slate-700 mb-3">Suggested settlements</h3>
                            <div className="flex flex-col gap-2">
                                {settlements.map((s, i) => (
                                    <div key={i} className="bg-amber-50 border border-amber-100 rounded-xl px-5 py-3 flex items-center justify-between">
                                        <div className="text-sm text-slate-700">
                                            <span className="font-semibold text-red-600">{userName(s.from, allUsers)}</span>
                                            <span className="text-slate-400 mx-2">→</span>
                                            <span className="font-semibold text-emerald-600">{userName(s.to, allUsers)}</span>
                                        </div>
                                        <Badge color="amber">{s.amount.toFixed(2)}</Badge>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}

// ─── Settings / Profile ───────────────────────────────────────────────────────

function ProfileModal({ me, onClose, onLogout }: { me: User; onClose: () => void; onLogout: () => void }) {
    const [name, setName] = useState(me.name);
    const [account, setAccount] = useState(me.account_number ?? "");
    const [pin, setPin] = useState("");
    const [loading, setLoading] = useState(false);
    const [err, setErr] = useState("");
    const [ok, setOk] = useState(false);

    async function save(e: React.FormEvent) {
        e.preventDefault();
        setErr(""); setOk(false); setLoading(true);
        try {
            await api("/me", {
                method: "PUT",
                body: JSON.stringify({
                    name: name || undefined,
                    account_number: account || undefined,
                    pin_code: pin || undefined,
                }),
            });
            setOk(true); setPin("");
        } catch (e: any) {
            setErr(e.message);
        } finally {
            setLoading(false);
        }
    }

    async function deleteAccount() {
        if (!confirm("Delete your account? This cannot be undone.")) return;
        await api("/me", { method: "DELETE" });
        onLogout();
    }

    return (
        <Modal title="Your profile" onClose={onClose}>
            <form onSubmit={save} className="flex flex-col gap-4">
                {err && <ErrorBox msg={err} onClose={() => setErr("")} />}
                {ok && <div className="bg-emerald-50 text-emerald-700 rounded-lg px-4 py-2 text-sm">Saved!</div>}
                <Input label="Name" value={name} onChange={e => setName(e.target.value)} />
                <Input label="Account number" value={account} onChange={e => setAccount(e.target.value)} placeholder="IBAN" />
                <Input label="New PIN (leave blank to keep current)" type="password" inputMode="numeric" maxLength={4} value={pin} onChange={e => setPin(e.target.value)} placeholder="••••" />
                <div className="flex justify-between gap-2 pt-2">
                    <Btn type="button" variant="danger" onClick={deleteAccount}>Delete account</Btn>
                    <Btn type="submit" disabled={loading}>{loading ? "Saving…" : "Save changes"}</Btn>
                </div>
            </form>
        </Modal>
    );
}

// ─── App shell ────────────────────────────────────────────────────────────────

const NAV_ITEMS: { view: View; label: string; icon: string }[] = [
    { view: "events", label: "Events", icon: "🗓" },
    { view: "transactions", label: "Transactions", icon: "🧾" },
    { view: "balances", label: "Balances", icon: "⚖️" },
];

export default function App() {
    const [authView, setAuthView] = useState<"login" | "register">("login");
    const [me, setMe] = useState<User | null>(null);
    const [allUsers, setAllUsers] = useState<User[]>([]);
    const [view, setView] = useState<View>("events");
    const [showProfile, setShowProfile] = useState(false);
    const [booting, setBooting] = useState(true);

    // Try restoring session on mount
    useEffect(() => {
        api<User>("/me")
            .then(user => {
                setMe(user);
                return api<User[]>("/admin/users").catch(() => [user]);
            })
            .then(users => setAllUsers(users))
            .catch(() => { })
            .finally(() => setBooting(false));
    }, []);

    async function handleLogin(user: User) {
        setMe(user);
        // Try to load all users for participant selection; fall back to just self
        const users = await api<User[]>("/admin/users").catch(() => [user]);
        setAllUsers(users);
        setView("events");
    }

    function handleLogout() {
        setMe(null);
        setAllUsers([]);
        setAuthView("login");
    }

    if (booting) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-slate-50">
                <Spinner />
            </div>
        );
    }

    if (!me) {
        if (authView === "register") {
            return <RegisterForm onSuccess={handleLogin} goLogin={() => setAuthView("login")} />;
        }
        return <LoginForm onSuccess={handleLogin} goRegister={() => setAuthView("register")} />;
    }

    return (
        <div className="min-h-screen bg-slate-50">
            {/* Top nav */}
            <header className="sticky top-0 z-40 bg-white border-b border-slate-100 shadow-sm">
                <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <span className="text-xl">💸</span>
                        <span className="font-bold text-slate-900 tracking-tight">MMA</span>
                    </div>
                    <nav className="flex gap-1">
                        {NAV_ITEMS.map(item => (
                            <button
                                key={item.view}
                                onClick={() => setView(item.view)}
                                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${view === item.view
                                    ? "bg-indigo-600 text-white"
                                    : "text-slate-600 hover:bg-slate-100"
                                    }`}
                            >
                                <span>{item.icon}</span>
                                <span className="hidden sm:inline">{item.label}</span>
                            </button>
                        ))}
                    </nav>
                    <button
                        onClick={() => setShowProfile(true)}
                        className="w-9 h-9 rounded-full bg-indigo-100 text-indigo-700 font-bold text-sm flex items-center justify-center hover:bg-indigo-200 transition-colors"
                    >
                        {me.name[0].toUpperCase()}
                    </button>
                </div>
            </header>

            {/* Main */}
            <main className="max-w-3xl mx-auto px-4 py-6">
                {view === "events" && <EventsView me={me} allUsers={allUsers} />}
                {view === "transactions" && <TransactionsView me={me} allUsers={allUsers} />}
                {view === "balances" && <BalancesView me={me} allUsers={allUsers} />}
            </main>

            {showProfile && (
                <ProfileModal
                    me={me}
                    onClose={() => setShowProfile(false)}
                    onLogout={handleLogout}
                />
            )}
        </div>
    );
}