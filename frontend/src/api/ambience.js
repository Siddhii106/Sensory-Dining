const BASE = "/api/orders";

async function request(path, {method = "GET", body, token } = {}) {
    const response = await fetch(`${BASE}${path}`, {
        method,
        headers: {
            "Content-Type": "application/json",
            Authorization: `Token ${token}`,
        },
        body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        const error = new Error(data.detail ?? "Something went wrong. Please try again.");
        error.status = response.status;
        throw error;
    }
    return response.json();
}

export async function getAmbienceSession(orderId, token) {
    try {
        return await request(`/${orderId}/ambience/`, { token });
    } catch (err) {
        if (err.status === 404) return null;
        throw err;
    }
}
export const createAmbienceSession = (orderId, vibe, token) =>
    request(`/${orderId}/ambience/`, { method: "POST", body: vibe, token });

export const sendAmbienceControl = (orderId, action, token) => 
    request(`/${orderId}/ambience/control/`, {method:"POST", body: { action }, token });