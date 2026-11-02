precision highp float;
uniform sampler2D uTexSampler;
varying vec2 vTexSamplingCoord;
uniform float uWidth;
uniform float uHeight;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
uniform float uControl4;
uniform float uControl5;
uniform float uControl6;
uniform float uControl7;
uniform float uControl8;

void main() {
    const float northWest = 0.0;
    const float northEast = 0.0;
    const float southWest = 0.0;
    const float southEast = 0.0;
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec2 px = vec2(1.0 / max(uWidth, 1.0),
                   1.0 / max(uHeight, 1.0));
    vec4 source = texture2D(uTexSampler, uv);
    float center = 1.0 + 0.5 * uControl2;
    float north = 0.5 * uControl3;
    float west = 0.5 * uControl4;
    float east = 0.5 * uControl5;
    float south = 0.5 * uControl6;
    vec4 sum = source * center;
    sum += texture2D(uTexSampler, clamp(uv + vec2(-px.x, px.y), 0.0, 1.0)) * northWest;
    sum += texture2D(uTexSampler, clamp(uv + vec2(0.0, px.y), 0.0, 1.0)) * north;
    sum += texture2D(uTexSampler, clamp(uv + px, 0.0, 1.0)) * northEast;
    sum += texture2D(uTexSampler, clamp(uv - vec2(px.x, 0.0), 0.0, 1.0)) * west;
    sum += texture2D(uTexSampler, clamp(uv + vec2(px.x, 0.0), 0.0, 1.0)) * east;
    sum += texture2D(uTexSampler, clamp(uv - px, 0.0, 1.0)) * southWest;
    sum += texture2D(uTexSampler, clamp(uv - vec2(0.0, px.y), 0.0, 1.0)) * south;
    sum += texture2D(uTexSampler, clamp(uv + vec2(px.x, -px.y), 0.0, 1.0)) * southEast;
    vec4 value = sum * exp2(uControl7) + vec4(0.25 * uControl8);
    vec4 effected = floor(clamp(value, 0.0, 1.0) * 255.0 + 0.00001) / 255.0;
    gl_FragColor = clamp(mix(source, effected, clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
