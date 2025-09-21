import LeanPlayground.Basic

-------------------------------------------------------------
-- Theorem 1: Identity of addition
-- Statement: For any natural number n, n + 0 = n
-------------------------------------------------------------
theorem add_zero (n : Nat) : n + 0 = n := by
  induction n
  case zero =>
    -- Base case: 0 + 0 = 0
    rfl
  case succ n ih =>
    -- succ n + 0 = succ (n + 0)
    -- by induction hypothesis, n + 0 = n
    rw [Nat.add_zero]

-------------------------------------------------------------
-- Theorem 2: Commutativity of addition
-- Statement: For any natural numbers a, b, a + b = b + a
-------------------------------------------------------------
theorem add_comm (a b : Nat) : a + b = b + a := by
  induction a
  case zero =>
    -- Base case: 0 + b = b = b + 0
    rw [Nat.zero_add, Nat.add_zero]
  case succ a ih =>
    -- succ a + b = succ (a + b)
    -- use induction hypothesis: a + b = b + a
    rw [Nat.succ_add, ih, ←Nat.add_succ]

-------------------------------------------------------------
-- Theorem 3: Associativity of addition
-- Statement: For any natural numbers a, b, c,
-- (a + b) + c = a + (b + c)
-------------------------------------------------------------
theorem add_assoc (a b c : Nat) : (a + b) + c = a + (b + c) := by
  induction a
  case zero =>
    -- Base case: (0 + b) + c = b + c = 0 + (b + c)
    rw [Nat.zero_add, Nat.zero_add]   -- rewrite both sides
  case succ a ih =>
    -- Inductive step: (succ a + b) + c = succ ((a + b) + c)
    -- By IH: (a + b) + c = a + (b + c)
    -- So succ (...) = succ (a + (b + c)) = (succ a + (b + c))
    rw [Nat.succ_add, Nat.succ_add, ih]

-------------------------------------------------------------
-- Theorem 4: Distributivity of multiplication over addition
-- Statement: For any a b c, a * (b + c) = a * b + a * c
-------------------------------------------------------------
theorem mul_distrib (a b c : Nat) : a * (b + c) = a * b + a * c := by
  induction a
  case zero =>
    -- Base case: 0 * (b + c) = 0 = 0 + 0
    rw [Nat.zero_mul, Nat.zero_mul, Nat.zero_mul, Nat.zero_add]
  case succ a ih =>
    -- succ a * (b + c) = (a * (b + c)) + (b + c)
    -- apply induction hypothesis
    rw [Nat.succ_mul, ih, Nat.succ_mul, Nat.succ_mul, Nat.add_assoc]

-------------------------------------------------------------
-- Theorem 5: Zero multiplication
-- Statement: For any natural number n, 0 * n = 0
-------------------------------------------------------------
theorem zero_mul (n : Nat) : 0 * n = 0 := by
  -- By definition, 0 * n = 0
  induction n
  case zero =>
    -- Base case: 0 * 0 = 0
    rfl
  case succ n ih =>
    -- Step: 0 * (n+1) = 0 * n + 0 = 0 + 0 = 0
    rw [Nat.mul_succ, ih, Nat.zero_add]

-------------------------------------------------------------
-- Theorem 6: Multiplication by one
-- Statement: For any natural number n, n * 1 = n
-------------------------------------------------------------
theorem mul_one (n : Nat) : n * 1 = n := by
  induction n
  case zero =>
    -- Base: 0 * 1 = 0
    rfl
  case succ n ih =>
    -- Step: (n+1) * 1 = n * 1 + 1 = n + 1
    rw [Nat.succ_mul, ih]

-------------------------------------------------------------
-- Theorem 7: Commutativity of multiplication
-- Statement: For any natural numbers a, b, a * b = b * a
-------------------------------------------------------------
theorem mul_comm (a b : Nat) : a * b = b * a := by
  induction a
  case zero =>
    -- Base: 0 * b = 0 = b * 0
    rw [Nat.zero_mul, Nat.mul_zero]
  case succ a ih =>
    -- Step: (a+1) * b = a * b + b
    -- By induction hypothesis: a * b = b * a
    rw [Nat.succ_mul, ih, Nat.mul_succ]

-------------------------------------------------------------
-- Theorem 8: Associativity of multiplication
-- Statement: For any a, b, c, (a * b) * c = a * (b * c)
-------------------------------------------------------------
theorem mul_assoc (a b c : Nat) : (a * b) * c = a * (b * c) := by
  induction a
  case zero =>
    -- Base: (0 * b) * c = 0 = 0 * (b * c)
    rw [Nat.zero_mul, Nat.zero_mul]
  case succ a ih =>
    -- Step: ((a+1) * b) * c = (a*b + b) * c
    -- Expand and use induction hypothesis
    rw [Nat.succ_mul, Nat.add_mul, ih, Nat.mul_add, Nat.succ_mul]


-------------------------------------------------------------
-- Lemma 1: add_le_add_right
-- Statement: For any natural numbers a, b, c:
-- if a ≤ b, then a + c ≤ b + c
-------------------------------------------------------------
theorem add_le_add_right (a b c : Nat) (h : a ≤ b) : a + c ≤ b + c := by
  induction c with
  | zero =>
    -- Case c = 0: reduces to a ≤ b, which is our assumption
    rw [Nat.add_zero, Nat.add_zero]
    exact h
  | succ c ih =>
    -- Case c = succ c: 
    -- a + succ c = succ (a + c), b + succ c = succ (b + c)
    rw [Nat.add_succ, Nat.add_succ]
    -- succ preserves inequality
    apply Nat.succ_le_succ ih

-------------------------------------------------------------
-- Lemma 2: mul_le_mul_left
-- Statement: For any a, b, c: if a ≤ b and 0 < c, then c * a ≤ c * b
-------------------------------------------------------------
theorem mul_le_mul_left (a b c : Nat) (h : a ≤ b) (hc : 0 < c) : c * a ≤ c * b := by
  induction h with
  | refl =>
    -- Case: a = b → c * a ≤ c * a
    exact Nat.le_refl (c * a)
  | step h ih =>
    -- Case: a ≤ b → a ≤ b + 1
    calc
      c * a ≤ c * b := ih
      _ ≤ c * b + c := Nat.le_add_right (c * b) c
      _ = c * (b + 1) := by rw [Nat.mul_succ]
