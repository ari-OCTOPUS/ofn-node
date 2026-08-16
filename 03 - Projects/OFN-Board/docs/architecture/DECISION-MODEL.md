# Decision Model

Lead score: `S(l)=wv*V+wi*I+wg*G+wt*T+wq*Q-wr*R-wc*C` with every component normalized to `[0,1]` and explanation bullets.

Source score: `Q(s)=wI*Intent+wX*Exclusivity+wE*Evidence+wO*OperationalFit+wA*Automation-wC*Cost-wR*Risk`.

Agent utility: `U(a,c)=Capability*Trust*ExpectedValue-Cost-Risk` after hard constraints.

Trust update: `Trust(t+1)=clip((1-alpha)*Trust(t)+alpha*OutcomeQuality,0,1)`, alpha default 0.05-0.15, with minimum samples before routing changes.

No GNN/RL in MVP. Use transparent rules and calibrate after labelled outcomes.
