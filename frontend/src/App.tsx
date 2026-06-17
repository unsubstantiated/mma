'use client'

import { useEffect, useState } from "react";

async function get_events() {
    const response = await fetch("http://localhost:8000/events");
    return await response.json();
}

export default function App() {
    const [data, setData] = useState(null);

    useEffect(() => {
        get_events().then(setData);
    }, []);

    return (
        <div>
            {JSON.stringify(data)}
        </div>
    );
}