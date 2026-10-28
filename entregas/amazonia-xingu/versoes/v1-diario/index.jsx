import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {AltamiraVideo} from './video';
import {ATMVideo, ATMShortVideo} from './atm-video';
import {XinguVideo} from './xingu-video';

const Root = () => (
  <>
    <Composition id="PulsoAmazoniaXingu" component={XinguVideo} durationInFrames={4500} fps={30} width={1920} height={1080}/>
    <Composition id="PulsoAmazoniaXinguPrevia" component={XinguVideo} durationInFrames={750} fps={30} width={1920} height={1080} defaultProps={{preview:true}}/>
    {/* Composição principal unificada: 2700 frames (90s @ 30fps) Full-Bleed 1080p */}
    <Composition
      id="PulsoATM2026"
      component={ATMVideo}
      durationInFrames={2700}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="PulsoATM2026Curto"
      component={ATMShortVideo}
      durationInFrames={2700}
      fps={30}
      width={1920}
      height={1080}
    />
    <Composition
      id="PulsoATMPrevia"
      component={ATMVideo}
      durationInFrames={570}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{preview: true}}
    />
    <Composition
      id="Altamira2026"
      component={AltamiraVideo}
      durationInFrames={1800}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{testMode: false}}
    />
    <Composition
      id="AltamiraTeste"
      component={AltamiraVideo}
      durationInFrames={180}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{testMode: true}}
    />
  </>
);

registerRoot(Root);
