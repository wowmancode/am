precision highp float;

uniform sampler2D uTexSampler;
uniform float uTime;
uniform float uWidth;
uniform float uHeight;
uniform float uControl1;
uniform float uControl2;
uniform float uControl3;
varying vec2 vTexSamplingCoord;

vec4 frameBytes(float value) {
    return mod(floor(vec4(value, value / 256.0,
                         value / 65536.0, value / 16777216.0)), 256.0);
}

vec4 frameSeed(float frame) {
    vec4 a = frameBytes(frame);
    vec4 b = frameBytes(frame * 8.0);
    vec4 exclusive = vec4(0.0);
    float place = 1.0;
    for (int bit = 0; bit < 8; ++bit) {
        exclusive += mod(mod(a, 2.0) + mod(b, 2.0), 2.0) * place;
        a = floor(a * 0.5);
        b = floor(b * 0.5);
        place *= 2.0;
    }
    return vec4(255.0) - exclusive;
}

float nextRandom(inout vec4 state) {
    float a = state.x * 253.0 + 195.0;
    float b = state.y * 253.0 + state.x * 67.0 + 158.0 + floor(a / 256.0);
    float c = state.z * 253.0 + state.y * 67.0 + state.x * 3.0 +
              38.0 + floor(b / 256.0);
    float d = state.w * 253.0 + state.z * 67.0 + state.y * 3.0 + floor(c / 256.0);
    state = mod(vec4(a, b, c, d), 256.0);
    return mod(state.w, 128.0) * 256.0 + state.z;
}

vec3 reflectedStep(vec3 current, vec3 delta, float bound) {
    vec3 next = current + delta;
    if (next.x > bound) next.x = bound - (next.x - bound);
    else if (next.x < -bound) next.x = (-bound - next.x) - bound;
    if (next.y > bound) next.y = bound - (next.y - bound);
    else if (next.y < -bound) next.y = (-bound - next.y) - bound;
    if (next.z > bound) next.z = bound - (next.z - bound);
    else if (next.z < -bound) next.z = (-bound - next.z) - bound;
    return next;
}

void nativeMotion(float frame, float bound, float velocity,
                  out vec3 motion, out vec2 previous, out float blur) {
    motion = vec3(0.0);
    previous = vec2(0.0);
    blur = 0.0;
    float start = max(frame - 4096.0, 0.0);
    float distance = velocity * bound;
    for (int index = 0; index < 4096; ++index) {
        float at = start + float(index);
        if (at >= frame) break;
        vec4 state = frameSeed(at);
        float x = nextRandom(state);
        float y = nextRandom(state);
        float angle = nextRandom(state);
        float extra = nextRandom(state);
        previous = motion.xy;
        vec3 delta = (mod(vec3(x, y, angle), 255.0) * 0.00390625 *
                      distance) * 2.0 - vec3(distance);
        motion = reflectedStep(motion, delta, bound);
        blur = max(mod(extra, 4.0) - 2.0, 0.0);
    }
}

vec4 pixelColor(vec2 pixel, vec2 size) {
    vec2 uv = (clamp(pixel, vec2(0.0), size - vec2(1.0)) + vec2(0.5)) / size;
    uv.y = 1.0 - uv.y;
    return texture2D(uTexSampler, clamp(uv, 0.0, 1.0));
}

vec4 shiftedImage(vec2 pixel, vec2 size, vec2 offset, float angle) {
    vec2 center = size * 0.5;
    vec2 p = pixel - center - offset * size;
    float ca = cos(angle);
    float sa = sin(angle);
    vec2 mapped = vec2(dot(p, vec2(ca, sa)),
                       dot(p, vec2(-sa, ca))) / 1.18 + center;
    if (mapped.x < 0.0 || mapped.y < 0.0 ||
        mapped.x > size.x - 1.0 || mapped.y > size.y - 1.0) return vec4(0.0);
    vec2 first = floor(mapped);
    vec2 weight = mapped - first;
    vec4 top = mix(pixelColor(first, size),
                   pixelColor(first + vec2(1.0, 0.0), size), weight.x);
    vec4 bottom = mix(pixelColor(first + vec2(0.0, 1.0), size),
                      pixelColor(first + vec2(1.0, 1.0), size), weight.x);
    return mix(top, bottom, weight.y);
}

void main() {
    vec2 uv = clamp(vTexSamplingCoord, 0.0, 1.0);
    vec4 source = texture2D(uTexSampler, uv);
    vec2 size = vec2(max(uWidth, 1.0), max(uHeight, 1.0));
    vec2 pixel = vec2(uv.x, 1.0 - uv.y) * size - vec2(0.5);
    float bound = clamp(0.99 * exp2(uControl2), 0.0, 1.0) * 0.06;
    float velocity = clamp(0.99 * exp2(uControl3), 0.0, 1.0);
    float frame = floor(max(uTime, 0.0) * 30.0 + 0.00001);
    vec3 motion;
    vec2 previous;
    float blur;
    nativeMotion(frame, bound, velocity, motion, previous, blur);
    vec4 result = shiftedImage(pixel, size, motion.xy, motion.z);
    if (blur > 0.5) {
        result = mix(result, shiftedImage(pixel, size, previous, motion.z), 0.5);
    }
    gl_FragColor = clamp(mix(source, result, clamp(uControl1, 0.0, 1.0)), 0.0, 1.0);
}
