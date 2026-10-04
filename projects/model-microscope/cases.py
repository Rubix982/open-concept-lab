"""The prepared cases. `target` is the next word we watch (with its leading
space); `corrupt` is the part of the prompt that causal tracing scrambles."""

CASES = [
    # ---- facts: where is the fact stored?
    dict(id="eiffel", group="Facts", title="Where is the Eiffel Tower?",
         prompt="The Eiffel Tower is located in the city of", target=" Paris", corrupt="The Eiffel Tower"),
    dict(id="colosseum", group="Facts", title="Where is the Colosseum?",
         prompt="The Colosseum is located in the city of", target=" Rome", corrupt="The Colosseum"),
    dict(id="jordan", group="Facts", title="Michael Jordan's sport",
         prompt="Michael Jordan is a professional", target=" basketball", corrupt="Michael Jordan"),
    dict(id="iphone", group="Facts", title="Who makes the iPhone?",
         prompt="The iPhone is a smartphone made by", target=" Apple", corrupt="The iPhone"),
    dict(id="japan", group="Facts", title="The capital of Japan",
         prompt="The capital of Japan is the city of", target=" Tokyo", corrupt="Japan"),
    dict(id="shakespeare", group="Facts", title="Who wrote Hamlet?",
         prompt="The play Hamlet was written by William", target=" Shakespeare", corrupt="Hamlet"),
    dict(id="windows", group="Facts", title="Who makes Windows?",
         prompt="Windows is an operating system developed by", target=" Microsoft", corrupt="Windows"),

    # ---- two steps: does it compose?
    dict(id="hop-eiffel", group="Two steps", title="The capital of the Eiffel Tower's country",
         prompt="The Eiffel Tower is in a country whose capital is", target=" Paris", corrupt="The Eiffel Tower"),
    dict(id="hop-sushi", group="Two steps", title="The language of sushi's country",
         prompt="Sushi comes from a country where people speak", target=" Japanese", corrupt="Sushi"),

    # ---- copying: in-context patterns
    dict(id="dursley", group="Copying", title="Copying a name it has seen",
         prompt="Mr. and Mrs. Dursley lived at number four. One morning Mr. Durs", target="ley", corrupt="Dursley lived"),
    dict(id="random", group="Copying", title="Repeating a random sequence",
         prompt="kettle orbit lemon fabric kettle orbit lemon", target=" fabric", corrupt="fabric kettle"),
    dict(id="ioi", group="Copying", title="Who gave the drink? (indirect object)",
         prompt="When Mary and John went to the store, John gave a drink to", target=" Mary", corrupt="Mary and"),

    # ---- language: grammar and meaning
    dict(id="plural", group="Language", title="Agreement across a clause",
         prompt="The keys to the old wooden cabinet", target=" were", corrupt="The keys"),
    dict(id="opposite", group="Language", title="The opposite of hot",
         prompt="The opposite of hot is", target=" cold", corrupt="hot"),
    dict(id="years", group="Language", title="A later year",
         prompt="The war lasted from the year 1732 to the year 17", target="45", corrupt="1732"),

    # ---- where it goes wrong
    dict(id="arith", group="Where it fails", title="Adding two numbers",
         prompt="23 + 45 =", target=" 68", corrupt="23 + 45"),
    dict(id="negation", group="Where it fails", title="A fact, negated",
         prompt="The Eiffel Tower is not located in the city of", target=" Paris", corrupt="The Eiffel Tower"),
    dict(id="recent", group="Where it fails", title="A fact that changed after training",
         prompt="The current CEO of Twitter is", target=" Jack", corrupt="Twitter"),
]
