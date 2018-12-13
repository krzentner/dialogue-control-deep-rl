Goal Inference
==============

The module `goal_inference.py` infers goals using a distributional
representation of knowledge. At all time in the dialogue, it maintains two
vectors. One of those vectors represents the confidence that the user has each
goal, the other vector indicates the confidence that the user does not have the
goal.

Each utterance that the user makes results in both vectors being update, and
then them being updated to be consistent with each other.

The module provides a back channel, which indicates if the user has provided
irrelevant information, information which improves the inference, or
information which is inconsistent with the current inference distribution.

Example Dialogues using `goal_inference.py`:
=================

#Slot filling like dialogue:

```
Please provide act,goal abbreviation pairs:
Input: G,G
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Okay.
Input: G,C
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Okay.
Input: G,R
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCONFIRMED
Is your goal to create the Gold Crown with Ruby ?
Input: C
Inference state before: InferenceState.UNCONFIRMED
Inference state after: InferenceState.CONFIRMED
Great! Let's make the Gold Crown with Ruby !
```

#Detecting inconsistencies by distribution collapse:

```
Please provide act,goal abbreviation pairs:
Input: G,G
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Okay.
Input: G,G
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Of course.
Input: G,S
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.CONFUSED
Wait what? Let's start over.
Input: G,G
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Okay.
Input: G,R
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Okay.
Input: G,J
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.CONFUSED
Wait what? Let's start over.
Input: G,G
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Okay.
Input: G,C
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Okay.
Input: G,R
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCONFIRMED
Is your goal to create the Gold Crown with Ruby ?
Input: D
Inference state before: InferenceState.UNCONFIRMED
Inference state after: InferenceState.UNCERTAIN
Wait what? Let's start over.
Input: G,C
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Okay.
Input: G,SD
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCONFIRMED
Is your goal to create the Silver Crown with Diamond ?
Input: C
Inference state before: InferenceState.UNCONFIRMED
Inference state after: InferenceState.CONFIRMED
Great! Let's make the Silver Crown with Diamond !
```

# Overanswering:

```
Please provide act,goal abbreviation pairs:
Input: G,SBA
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCONFIRMED
Is your goal to create the Silver Bracelet with Amethyst ?
Input: C
Inference state before: InferenceState.UNCONFIRMED
Inference state after: InferenceState.CONFIRMED
Great! Let's make the Silver Bracelet with Amethyst !
```

# Redundant Information:

```
Please provide act,goal abbreviation pairs:
Input: G,G
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Okay.
Input: G,G
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCERTAIN
Of course.
Input: G,CR
Inference state before: InferenceState.UNCERTAIN
Inference state after: InferenceState.UNCONFIRMED
Is your goal to create the Gold Crown with Ruby ?
Input: C
Inference state before: InferenceState.UNCONFIRMED
Inference state after: InferenceState.CONFIRMED
Great! Let's make the Gold Crown with Ruby !
```
