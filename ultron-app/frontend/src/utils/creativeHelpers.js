// Wake Word & Creative Module Functions

// Toggle wake word listening
export const toggleWakeWord = async (isEnabled, setIsWakeWordEnabled, setWakeWordStatus) => {
    try {
        if (isEnabled) {
            // Disable
            const response = await fetch('http://localhost:8000/wake_word/disable', { method: 'POST' })
            const data = await response.json()
            setIsWakeWordEnabled(false)
            setWakeWordStatus('Disabled')
        } else {
            // Enable
            const response = await fetch('http://localhost:8000/wake_word/enable', { method: 'POST' })
            const data = await response.json()
            if (data.success) {
                setIsWakeWordEnabled(true)
                setWakeWordStatus('Listening...')
            }
        }
    } catch (error) {
        console.error('Wake word toggle error:', error)
        setWakeWordStatus('Error')
    }
}

// Generate image
export const generateImage = async (prompt, setCreativeOutput, setLoading) => {
    setLoading(true)
    try {
        const response = await fetch(`http://localhost:8000/create/image?prompt=${encodeURIComponent(prompt)}`, {
            method: 'POST'
        })
        const data = await response.json()
        setCreativeOutput(data)
    } catch (error) {
        console.error('Image generation error:', error)
    } finally {
        setLoading(false)
    }
}

// Generate code
export const generateCode = async (description, language, setCreativeOutput, setLoading) => {
    setLoading(true)
    try {
        const response = await fetch(`http://localhost:8000/create/code?description=${encodeURIComponent(description)}&language=${language}`, {
            method: 'POST'
        })
        const data = await response.json()
        setCreativeOutput(data)
    } catch (error) {
        console.error('Code generation error:', error)
    } finally {
        setLoading(false)
    }
}

// Generate sound
export const generateSound = async (description, duration, setCreativeOutput, setLoading) => {
    setLoading(true)
    try {
        const response = await fetch(`http://localhost:8000/create/sound?description=${encodeURIComponent(description)}&duration=${duration}`, {
            method: 'POST'
        })
        const data = await response.json()
        setCreativeOutput(data)
    } catch (error) {
        console.error('Sound generation error:', error)
    } finally {
        setLoading(false)
    }
}
