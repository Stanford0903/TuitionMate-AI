
# TuitionMate AI — Human Handoff Flow

## Goal
Automatically answer verified FAQ questions.
Refer unknown or sensitive questions to human staff.

## Request Flow
1. Customer sends a question.
2. FastAPI validates the input.
3. System checks safety and FAQ rules.
4. If there is a verified FAQ match:
   - Return status: answered
   - Return handoff: false
   - Return the approved FAQ answer
5. Otherwise:
   - Return status: handoff
   - Return handoff: true
   - Provide a safe fallback message
6. If a real staff notification system is
   connected later, create a handoff ticket.

## Human Handoff Triggers
- No verified FAQ answer
- Refunds or payment disputes
- Complaints
- Special learning needs
- Personal or sensitive information
- Explicit request to speak with staff

## Example: Answered
{
  "status": "answered",
  "handoff": false,
  "reply": "Our demo centre offers Maths, Science and English."
}

## Example: Handoff
{
  "status": "handoff",
  "handoff": true,
  "reply": "I cannot confirm that information. Please contact our staff for assistance."
}

## Important
handoff: true does not mean staff have
already received or accepted the request.
