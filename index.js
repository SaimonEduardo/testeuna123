enterCounterSpan = document.getElementById('entraram');
exitCounterSpan = document.getElementById('sairam');

enterCounter = 0
exitCounter = 0

const ws = new WebSocket("ws://localhost:8001");

ws.addEventListener('error', () => { throw new Error() });

ws.addEventListener('open', () => console.log("Connected"));

ws.addEventListener('message', ({ data }) => {
    dataToString = (data.toString('utf8'));
    formatedData = JSON.parse(dataToString);

    if (formatedData.payload === "ENTER") {
        enterCounterSpan.innerText = Number(++enterCounter)
    }

    if (formatedData.payload === "EXIT") {
        exitCounterSpan.innerText = Number(++exitCounter)
    }
})