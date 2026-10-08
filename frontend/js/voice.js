
const MethuVoice = {
    audio: null,

    async speak(text) {
        this.stop();

        try {
            console.log("METHU generating Gemini voice...");

            const response = await fetch(
                "http://127.0.0.1:8000/api/voice/speak",
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ text })
                }
            );

            if (!response.ok) {
                throw new Error(`Voice API error: ${response.status}`);
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);

            const audio = new Audio(url);
            this.audio = audio;

            // Reuse the browser audio context
            if (!this.audioContext) {
                this.audioContext = new AudioContext();
            }

            const source = this.audioContext.createMediaElementSource(audio);

            const analyser = this.audioContext.createAnalyser();
            analyser.fftSize = 1024;
            analyser.smoothingTimeConstant = 0.45;

            source.connect(analyser);
            analyser.connect(this.audioContext.destination);

            // Send analyser to hologram.js
            window.dispatchEvent(
                new CustomEvent("methu:audio-analyser", {
                    detail: { analyser }
                })
            );

            audio.onplay = () => {
                console.log("METHU started speaking");
                window.dispatchEvent(
                    new Event("methu:speech-start")
                );
            };

            const finish = () => {
                window.dispatchEvent(
                    new Event("methu:speech-end")
                );
                URL.revokeObjectURL(url);
                if (this.audio === audio) this.audio = null;
            };

            audio.onended = finish;
            audio.onerror = finish;


            await this.audioContext.resume();

            await audio.play();

        } catch (error) {
            console.error("METHU Voice Error:", error);
        }
    },

    stop() {
        if (this.audio) {
            this.audio.pause();
            this.audio.dispatchEvent(new Event("ended"));
            this.audio = null;
        }
    }
};

window.MethuVoice = MethuVoice;
