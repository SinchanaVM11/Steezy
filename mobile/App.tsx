import { NavigationContainer } from "@react-navigation/native";
import { createNativeStackNavigator } from "@react-navigation/native-stack";
import { StatusBar } from "expo-status-bar";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { HealthStatus } from "./src/api/health";
import { API_BASE_URL, USER_ID } from "./src/config";
import { useWardrobe } from "./src/wardrobe/useWardrobe";
import { FEEDBACK_ACTIONS } from "./src/api/feedback";
import { FeedbackSubmissionState, useFeedback } from "./src/feedback/useFeedback";

type RootStackParamList = {
  Home: undefined;
  Wardrobe: undefined;
  Inspiration: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const FEEDBACK_LABELS: Record<(typeof FEEDBACK_ACTIONS)[number], string> = {
  like: "Like",
  dislike: "Dislike",
  save: "Save",
  skip: "Skip",
  wear: "Wear",
  not_relevant: "Not relevant",
};

function HomeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.eyebrow}>STEEZY</Text>
      <Text style={styles.title}>Your fashion intelligence workspace.</Text>
      <Text style={styles.body}>
        The app shell is ready. Wardrobe and inspiration features will be
        connected to API-backed state in later phases.
      </Text>
      <HealthStatus />
    </View>
  );
}

function PlaceholderScreen({ title, description }: { title: string; description: string }) {
  return (
    <View style={styles.container}>
      <Text style={styles.eyebrow}>NEXT PHASE</Text>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.body}>{description}</Text>
    </View>
  );
}

function WardrobeScreen() {
  const { state, reload } = useWardrobe(USER_ID, API_BASE_URL);
  const { submit, stateFor } = useFeedback(USER_ID, API_BASE_URL);

  return (
    <View style={styles.container}>
      <Text style={styles.eyebrow}>WARDROBE</Text>
      <Text style={styles.title}>Your pieces.</Text>
      {state.status === "loading" && <Text style={styles.body}>Loading wardrobe…</Text>}
      {state.status === "empty" && (
        <Text style={styles.body}>Your wardrobe is empty. Add a garment through the API to get started.</Text>
      )}
      {state.status === "error" && (
        <>
          <Text style={styles.body}>Wardrobe unavailable: {state.message}</Text>
          <Text accessibilityRole="button" onPress={() => void reload()} style={styles.action}>
            Try again
          </Text>
        </>
      )}
      {state.status === "success" && (
        <View>
          {state.items.map((item) => (
            <WardrobeItemView
              key={item.id}
              item={item}
              feedback={stateFor(item.id)}
              onSubmit={submit}
            />
          ))}
        </View>
      )}
    </View>
  );
}

function WardrobeItemView({
  item,
  feedback,
  onSubmit,
}: {
  item: {
    id: string;
    category: string;
    colors: string[];
  };
  feedback: FeedbackSubmissionState;
  onSubmit: ReturnType<typeof useFeedback>["submit"];
}) {
  return (
    <View style={styles.item}>
              <Text style={styles.body}>
                {item.category} · {item.colors.join(", ") || "color not specified"}
              </Text>
              <View style={styles.actions}>
                {FEEDBACK_ACTIONS.map((action) => {
                  return (
                    <Pressable
                      key={action}
                      disabled={feedback.status === "submitting"}
                      onPress={() => void onSubmit(item.id, action)}
                    >
                      <Text style={styles.action}>
                        {feedback.status === "submitting" ? "Saving…" : FEEDBACK_LABELS[action]}
                      </Text>
                    </Pressable>
                  );
                })}
              </View>
              {feedback.status === "success" && (
                <Text style={styles.feedbackSuccess}>Feedback saved.</Text>
              )}
              {feedback.status === "error" && (
                <Text style={styles.feedbackError}>
                  {feedback.message}
                </Text>
              )}
            </View>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="dark" />
      <Stack.Navigator>
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Wardrobe" component={WardrobeScreen} />
        <Stack.Screen name="Inspiration">
          {() => (
            <PlaceholderScreen
              title="Inspiration"
              description="Image understanding and retrieval will be introduced after the perception baseline is evaluated."
            />
          )}
        </Stack.Screen>
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    gap: 16,
    padding: 32,
    backgroundColor: "#F8F2E9",
  },
  eyebrow: {
    color: "#776B5D",
    fontSize: 12,
    fontWeight: "700",
    letterSpacing: 2,
  },
  title: {
    color: "#2F2A25",
    fontSize: 32,
    fontWeight: "700",
  },
  body: {
    color: "#5C534A",
    fontSize: 16,
    lineHeight: 24,
  },
  action: {
    color: "#6D4C41",
    fontSize: 16,
    fontWeight: "700",
  },
  item: {
    gap: 8,
  },
  actions: {
    flexDirection: "row",
    gap: 16,
  },
  feedbackSuccess: {
    color: "#3F6B4A",
    fontSize: 14,
  },
  feedbackError: {
    color: "#9B3A2E",
    fontSize: 14,
  },
});
