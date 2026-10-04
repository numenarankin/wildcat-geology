import { getConversations } from "@/lib/ai/conversations";
import { OrionWorkspace } from "@/components/ai/orion-workspace";
import { getAccount } from "@/lib/auth/account";
import { displayFirstName } from "@/lib/user";

export const metadata = { title: "Orion" };

export default async function OrionPage() {
  const [conversations, account] = await Promise.all([
    getConversations(),
    getAccount(),
  ]);
  const firstName = displayFirstName(account?.name ?? null, account?.email);

  return (
    <OrionWorkspace
      initialConversations={conversations}
      firstName={firstName}
    />
  );
}
