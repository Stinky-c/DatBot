from disnake import Embed, utils, Color

help_1 = (
    Embed(
        title="Supported Operations",
        timestamp=utils.utcnow(),
        description="Basic supported math operations",
        color=Color.random(7 * 2),
    )
    .add_field("Addition", "7+2 = 9")
    .add_field("Subtraction", "9-6 = 3")
    .add_field("Multiplication", "6*2 = 12")
    .add_field("Division", "9/2 = 4.5")
    .add_field("Divison (Integer)", "9//2 = 4")
    .add_field("Exponential", "3**2 = 9")
)
help_2 = (
    Embed(
        title="Supported Functions",
        timestamp=utils.utcnow(),
        description="Supported Math Functions",
        color=Color.random(6.283185307179586),
    )
    .add_field("Absolute Value", "abs(x)")
    .add_field("Logarithm (base ten)", "log10(x)")
    .add_field("Logarithm (default e)", "log(x, base)")
    .add_field("Square Root", "sqrt(x)")
    .add_field("Cosine (radians)", "cos(x)")
    .add_field("Sine (radians)", "sin(x)")
    .add_field("Tangent (radians)", "tan(x)")
    .add_field("Radians (degrees -> radians)", "rad(x)")
    .add_field("Degrees (radians -> degrees)", "deg(x)")
    .add_field("Round", "round(x,n)")
    .add_field("Combination", "nCr(n, r)")
    .add_field("Permutation", "nPr(n, r)")
)

help_embeds = (help_1, help_2)

# TODO:
"""

greatest common divisor (WIP): gcd([x,y,z])
least common multiple (WIP): lcm([x,y,z])

"""
