$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$speechAssembly = [System.Speech.Synthesis.SpeechSynthesizer].Assembly.Location
Add-Type -ReferencedAssemblies @($speechAssembly, 'System.Collections', 'System.ComponentModel.EventBasedAsync', 'System.Runtime') -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Speech.Synthesis;
public class PulsoWord {
    public string text;
    public double start;
    public double duration;
    public int char_start;
    public int char_count;
}
public class PulsoVoice {
    public static List<PulsoWord> Generate(string text, string path) {
        var words = new List<PulsoWord>();
        using (var synth = new SpeechSynthesizer()) {
            synth.SelectVoice("Microsoft Maria Desktop");
            synth.Rate = 0;
            synth.SetOutputToWaveFile(path);
            synth.SpeakProgress += (sender, e) => {
                words.Add(new PulsoWord { text=e.Text, start=e.AudioPosition.TotalSeconds, duration=0, char_start=e.CharacterPosition, char_count=e.CharacterCount });
            };
            synth.Speak(text);
            synth.SetOutputToNull();
        }
        for (int i=0; i<words.Count; i++) {
            words[i].duration = i+1<words.Count ? Math.Max(.05,words[i+1].start-words[i].start) : .35;
        }
        return words;
    }
}
'@
$taskSeriesRoot = $PSScriptRoot
$episodes = Get-Content -LiteralPath (Join-Path $taskSeriesRoot 'script.json') -Raw | ConvertFrom-Json
$taskSpeechDir = Join-Path $taskSeriesRoot 'speech'
New-Item -ItemType Directory -Path $taskSpeechDir -Force | Out-Null
foreach ($episode in $episodes) {
    for ($index=0; $index -lt $episode.scenes.Count; $index++) {
        $taskPhrases = $episode.scenes[$index].phrases
        if (-not $taskPhrases) { $taskPhrases = @($episode.scenes[$index]) }
        for ($phraseIndex=0; $phraseIndex -lt $taskPhrases.Count; $phraseIndex++) {
            $taskSuffix = if ($episode.scenes[$index].phrases) { '-p{0}' -f $phraseIndex } else { '' }
            $taskStem = Join-Path $taskSpeechDir ('e{0}-{1:00}{2}' -f $episode.episode,$index,$taskSuffix)
            $words = [PulsoVoice]::Generate($taskPhrases[$phraseIndex].text, "$taskStem.wav")
            $words | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$taskStem.json" -Encoding utf8
            Write-Output ('VOICE e{0}-{1:00}{2}: {3} words' -f $episode.episode,$index,$taskSuffix,$words.Count)
        }
    }
}
